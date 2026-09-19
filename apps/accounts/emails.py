# =============================================================
# MonTour — apps/accounts/emails.py
# Emails transactionnels : vérification d'adresse, réinitialisation de mot de passe
# =============================================================

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail

from .models import EmailVerificationToken

logger = logging.getLogger('apps')


def build_frontend_url(request, param, token):
    """
    Lien envoyé par email : il ouvre l'application web (/?<param>=<token>), qui
    appelle ensuite l'API en POST. Le token n'est donc jamais consommé par un
    simple GET (préchargement par un antivirus / client mail).
    """
    base = settings.FRONTEND_URL
    if not base:
        # Repli pour le développement local uniquement (voir FRONTEND_URL dans settings)
        if not settings.DEBUG:
            logger.error("[EMAIL] FRONTEND_URL non défini : lien construit depuis l'en-tête Host (non fiable).")
        base = request.build_absolute_uri('/')
    return f"{base.rstrip('/')}/?{urlencode({param: token})}"


def _send(user, subject, body):
    """Envoie un email à l'utilisateur. Retourne True si l'envoi a réussi."""
    if not settings.DEBUG and settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
        logger.error(
            '[EMAIL] Aucun serveur SMTP configuré (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD) : '
            f'l\'email « {subject} » pour {user.email} n\'est PAS délivré.'
        )
        # On le dit à l'appelant : l'écran d'inscription proposera alors un renvoi
        return False
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except Exception as e:
        logger.error(f'[EMAIL] Échec d\'envoi « {subject} » à {user.email} : {e}')
        return False
    return True


def send_verification_email(request, user, resend=False):
    """
    Génère un nouveau token (invalide les précédents) et envoie l'email.
    Retourne True si l'envoi a réussi, False sinon (l'erreur est journalisée).
    """
    token = EmailVerificationToken.create_for_user(user)
    verify_url = build_frontend_url(request, 'verify_email', token.token)
    intro = (
        'Voici votre nouveau lien pour activer votre compte MonTour :'
        if resend else
        'Cliquez sur le lien ci-dessous pour activer votre compte MonTour :'
    )
    sent = _send(
        user,
        'Vérifiez votre adresse email — MonTour',
        f'Bonjour {user.username},\n\n'
        f'{intro}\n{verify_url}\n\n'
        f'Ce lien est valable 24 heures.\n\n'
        f'Si vous n\'avez pas créé de compte, ignorez cet email.\n\n'
        f'— L\'équipe MonTour',
    )
    if sent:
        logger.info(f'[VERIFY-EMAIL] Email de vérification envoyé à : {user.email}')
    return sent


def send_password_reset_email(request, user, token_str):
    """Envoie le lien de réinitialisation (valable 2 h)."""
    reset_url = build_frontend_url(request, 'reset_password', token_str)
    return _send(
        user,
        'Réinitialisation de votre mot de passe — MonTour',
        f'Bonjour {user.username},\n\n'
        f'Pour choisir un nouveau mot de passe, cliquez sur ce lien :\n{reset_url}\n\n'
        f'Ce lien est valable 2 heures.\n\n'
        f'Si vous n\'êtes pas à l\'origine de cette demande, ignorez cet email : '
        f'votre mot de passe actuel reste inchangé.\n\n'
        f'— L\'équipe MonTour',
    )
