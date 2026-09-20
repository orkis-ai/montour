# =============================================================
# MonTour — apps/notifications/sms.py
# Envoi de SMS (rappel « votre tour approche ») via un fournisseur interchangeable :
#   - twilio          (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM ou TWILIO_MESSAGING_SERVICE_SID)
#   - africastalking  (AT_USERNAME, AT_API_KEY, AT_SENDER_ID optionnel)
#   - console         (aucun envoi : le SMS est seulement journalisé — développement)
# Le fournisseur est détecté selon les variables présentes, ou forcé par SMS_PROVIDER.
# Un échec d'envoi n'interrompt JAMAIS l'action de l'usager ou de l'agent : il est journalisé.
# =============================================================

import logging
import re
import unicodedata
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger('apps')


@dataclass
class SMSResult:
    ok: bool
    provider: str
    message_id: str = ''
    error: str = ''


# ─── Numéros de téléphone ─────────────────────────────────────
def normalize_phone(raw):
    """
    Convertit un numéro béninois saisi par l'usager en format international E.164.
    Accepte : +229XXXXXXXX, XXXXXXXX (8 chiffres, ancien format), 01XXXXXXXX et
    +22901XXXXXXXX (10 chiffres, depuis le passage du Bénin à 10 chiffres).
    Retourne None si le numéro n'est pas exploitable.
    """
    if not raw:
        return None
    cleaned = re.sub(r'[\s\-\.\(\)]', '', str(raw))
    if cleaned.startswith('+229'):
        national = cleaned[4:]
    elif cleaned.startswith('00229'):
        national = cleaned[5:]
    else:
        national = cleaned
    if not national.isdigit():
        return None
    if len(national) == 8:
        national = ('01' + national) if settings.SMS_BENIN_TEN_DIGITS else national
    elif len(national) == 10 and national.startswith('01'):
        national = national if settings.SMS_BENIN_TEN_DIGITS else national[2:]
    else:
        return None
    return '+229' + national


def gsm_safe(text):
    """
    Retire accents et emoji : le SMS reste en alphabet GSM simple (160 caractères par
    segment au lieu de 70 en Unicode), donc moins cher et sans caractères illisibles.
    """
    decomposed = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    ascii_text = ascii_text.replace('’', "'").replace('–', '-').replace('—', '-')
    return ascii_text.encode('ascii', 'ignore').decode('ascii').strip()


# ─── Fournisseurs ─────────────────────────────────────────────
class ConsoleProvider:
    name = 'console'

    def send(self, to, text):
        logger.info(f'[SMS:console] à {to} : {text}')
        return SMSResult(ok=True, provider=self.name, message_id='console')


class TwilioProvider:
    name = 'twilio'

    def send(self, to, text):
        sid, token = settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
        data = {'To': to, 'Body': text}
        if settings.TWILIO_MESSAGING_SERVICE_SID:
            data['MessagingServiceSid'] = settings.TWILIO_MESSAGING_SERVICE_SID
        else:
            data['From'] = settings.TWILIO_FROM
        try:
            resp = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
                data=data, auth=(sid, token), timeout=settings.SMS_TIMEOUT,
            )
            body = resp.json() if resp.content else {}
        except (requests.RequestException, ValueError) as e:
            return SMSResult(ok=False, provider=self.name, error=f'Erreur réseau : {e}')
        if resp.status_code in (200, 201):
            return SMSResult(ok=True, provider=self.name, message_id=body.get('sid', ''))
        return SMSResult(
            ok=False, provider=self.name,
            error=f"HTTP {resp.status_code} {body.get('code', '')} {body.get('message', resp.text[:200])}".strip(),
        )


class AfricasTalkingProvider:
    name = 'africastalking'

    def send(self, to, text):
        base = 'api.sandbox.africastalking.com' if settings.AT_USERNAME == 'sandbox' else 'api.africastalking.com'
        data = {'username': settings.AT_USERNAME, 'to': to, 'message': text}
        if settings.AT_SENDER_ID:
            data['from'] = settings.AT_SENDER_ID
        try:
            resp = requests.post(
                f'https://{base}/version1/messaging', data=data,
                headers={'apiKey': settings.AT_API_KEY, 'Accept': 'application/json'},
                timeout=settings.SMS_TIMEOUT,
            )
            body = resp.json() if resp.content else {}
        except (requests.RequestException, ValueError) as e:
            return SMSResult(ok=False, provider=self.name, error=f'Erreur réseau : {e}')
        recipients = (body.get('SMSMessageData') or {}).get('Recipients') or []
        if resp.status_code in (200, 201) and recipients and recipients[0].get('status') == 'Success':
            return SMSResult(ok=True, provider=self.name, message_id=recipients[0].get('messageId', ''))
        detail = recipients[0].get('status') if recipients else resp.text[:200]
        return SMSResult(ok=False, provider=self.name, error=f'HTTP {resp.status_code} {detail}')


def get_provider():
    """Fournisseur actif, ou None si la configuration est incomplète."""
    name = settings.SMS_PROVIDER
    if not name:
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            name = 'twilio'
        elif settings.AT_USERNAME and settings.AT_API_KEY:
            name = 'africastalking'
        else:
            name = 'console'
    if name == 'twilio':
        ok = settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and (
            settings.TWILIO_FROM or settings.TWILIO_MESSAGING_SERVICE_SID)
        return TwilioProvider() if ok else None
    if name == 'africastalking':
        ok = settings.AT_USERNAME and settings.AT_API_KEY
        return AfricasTalkingProvider() if ok else None
    if name == 'console':
        return ConsoleProvider()
    return None


# ─── Service ──────────────────────────────────────────────────
class SMSService:

    @classmethod
    def send(cls, to, text):
        """Envoie un SMS. Ne lève jamais d'exception."""
        provider = get_provider()
        if provider is None:
            return SMSResult(ok=False, provider='', error='Fournisseur SMS non configuré ou incomplet.')
        if isinstance(provider, ConsoleProvider) and not settings.DEBUG:
            # En production, « console » = personne ne reçoit rien : on ne fait pas semblant.
            logger.error('[SMS] Aucun fournisseur SMS configuré : SMS NON délivré (voir .env.example).')
            return SMSResult(ok=False, provider=provider.name, error='Aucun fournisseur SMS configuré.')
        try:
            return provider.send(to, gsm_safe(text))
        except Exception as e:  # sécurité : un fournisseur ne doit jamais casser l'appel d'un ticket
            logger.exception('[SMS] Erreur inattendue')
            return SMSResult(ok=False, provider=provider.name, error=f'Erreur inattendue : {e}')

    @classmethod
    def send_to_user(cls, user, text, kind, ticket=None):
        """
        Envoie un SMS à un usager s'il a un numéro valide et n'a pas désactivé les SMS.
        Journalise le résultat dans SMSLog. Retourne l'entrée SMSLog.
        """
        from .models import SMSLog

        def log(status, to='', provider='', message_id='', error=''):
            return SMSLog.objects.create(
                user=user, ticket=ticket, kind=kind, to=to, text=gsm_safe(text),
                provider=provider, status=status, provider_message_id=message_id, error=error,
            )

        if not settings.SMS_ENABLED:
            return log(SMSLog.STATUS_SKIPPED, error='SMS désactivés (SMS_ENABLED=False).')
        if not getattr(user, 'sms_notifications', True):
            return log(SMSLog.STATUS_SKIPPED, error='Usager : SMS désactivés dans son profil.')
        to = normalize_phone(user.phone)
        if not to:
            return log(SMSLog.STATUS_SKIPPED, error='Numéro de téléphone absent ou invalide.')

        result = cls.send(to, text)
        if result.ok:
            logger.info(f'[SMS] {kind} envoyé à {to} ({result.provider})')
            return log(SMSLog.STATUS_SENT, to, result.provider, result.message_id)
        logger.error(f'[SMS] Échec {kind} vers {to} : {result.error}')
        return log(SMSLog.STATUS_FAILED, to, result.provider, error=result.error)
