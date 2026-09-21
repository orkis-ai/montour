# =============================================================
# MonTour — apps/notifications/sms.py
# Envoi de SMS (rappel « votre tour approche ») via eSMS Africa (https://esmsafrica.io).
#   - esms     : clé API dans ESMS_API_KEY (voir .env.example)
#   - console  : aucun envoi, le SMS est seulement journalisé (développement)
# Sans clé API, le fournisseur « console » est utilisé ; en production il n'envoie rien
# et le signale. Un échec d'envoi n'interrompt JAMAIS l'action de l'usager ou de l'agent :
# il est journalisé (SMSLog + logs).
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
    +22901XXXXXXXX (10 chiffres : depuis le 30/11/2024 tous les numéros béninois
    portent le préfixe 01). Retourne None si le numéro n'est pas exploitable.
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


class ESMSAfricaProvider:
    """
    eSMS Africa — POST {ESMS_BASE_URL}/messages/send
    En-tête « Authorization: Bearer <clé> », corps JSON {to, text, sender_id?}.
    Réponse : {id, status (queued|submitted|delivered|failed), segments, cost, balance_after…}.
    Erreurs : 401 clé invalide, 402 solde insuffisant, 400/422 requête invalide, 429 cadence.
    """
    name = 'esms'

    ERRORS = {
        401: 'Clé API eSMS Africa refusée (ESMS_API_KEY invalide).',
        402: 'Solde eSMS Africa insuffisant : rechargez le compte.',
        429: 'Limite de cadence eSMS Africa atteinte.',
    }

    def send(self, to, text):
        payload = {'to': to, 'text': text}
        if settings.ESMS_SENDER_ID:
            payload['sender_id'] = settings.ESMS_SENDER_ID
        try:
            resp = requests.post(
                f"{settings.ESMS_BASE_URL.rstrip('/')}/messages/send",
                json=payload,
                headers={'Authorization': f'Bearer {settings.ESMS_API_KEY}', 'Accept': 'application/json'},
                timeout=settings.SMS_TIMEOUT,
            )
        except requests.RequestException as e:
            return SMSResult(ok=False, provider=self.name, error=f'Erreur réseau : {str(e)[:200]}')
        try:
            body = resp.json() if resp.content else {}
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}

        if resp.status_code in (200, 201, 202):
            if str(body.get('status', '')).lower() == 'failed':
                return SMSResult(ok=False, provider=self.name, message_id=str(body.get('id', '')),
                                 error=f"Refusé par eSMS Africa : {body.get('error_message') or 'échec'}")
            return SMSResult(ok=True, provider=self.name, message_id=str(body.get('id', '')))

        detail = self.ERRORS.get(resp.status_code) or (
            body.get('message') or body.get('error') or body.get('detail') or resp.text[:200]
        )
        return SMSResult(ok=False, provider=self.name, error=f'HTTP {resp.status_code} : {detail}')


def get_provider():
    """Fournisseur actif, ou None si la configuration est invalide."""
    name = settings.SMS_PROVIDER
    if not name:
        name = 'esms' if settings.ESMS_API_KEY else 'console'
    if name in ('esms', 'esmsafrica'):
        return ESMSAfricaProvider() if settings.ESMS_API_KEY else None
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
            return SMSResult(ok=False, provider='', error='Fournisseur SMS non configuré (ESMS_API_KEY manquante).')
        if isinstance(provider, ConsoleProvider) and not settings.DEBUG:
            # En production, « console » = personne ne reçoit rien : on ne fait pas semblant.
            logger.error('[SMS] Aucun fournisseur SMS configuré (ESMS_API_KEY) : SMS NON délivré.')
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
