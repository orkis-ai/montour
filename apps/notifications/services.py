# =============================================================
# MonTour — apps/notifications/services.py
# =============================================================

import logging
import requests
from django.conf import settings

logger = logging.getLogger('apps')


class NotificationService:
    """Envoi de notifications : base de données + Firebase FCM."""

    @classmethod
    def send(cls, user, notif_type: str, title: str, message: str, ticket=None):
        from .models import Notification
        notif = Notification.objects.create(
            user=user, type=notif_type,
            title=title, message=message, ticket=ticket,
        )
        cls._send_fcm(user, title, message, notif)
        return notif

    @classmethod
    def send_bulk(cls, users, notif_type: str, title: str, message: str):
        from .models import Notification
        notifications = [
            Notification(user=u, type=notif_type, title=title, message=message)
            for u in users
        ]
        Notification.objects.bulk_create(notifications)
        for u in users:
            cls._send_fcm(u, title, message)

    @classmethod
    def _send_fcm(cls, user, title: str, body: str, notif=None):
        server_key = settings.FIREBASE_SERVER_KEY
        if not server_key:
            logger.debug('[FCM] Clé serveur non configurée — ignoré.')
            return
        tokens = list(user.fcm_tokens.filter(is_active=True).values_list('token', flat=True))
        if not tokens:
            return
        payload = {
            'registration_ids': tokens,
            'notification': {'title': title, 'body': body, 'sound': 'default'},
            'data': {
                'notification_id': str(notif.id) if notif else '',
                'type': notif.type if notif else '',
            },
            'priority': 'high',
        }
        try:
            resp = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                json=payload,
                headers={'Authorization': f'key={server_key}', 'Content-Type': 'application/json'},
                timeout=5,
            )
            if resp.status_code == 200:
                logger.info(f'[FCM] Envoyé à {user.username} ({len(tokens)} appareil(s))')
            else:
                logger.warning(f'[FCM] HTTP {resp.status_code}: {resp.text}')
        except requests.RequestException as e:
            logger.error(f'[FCM] Erreur: {e}')