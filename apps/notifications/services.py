# =============================================================
# MonTour — apps/notifications/services.py
# =============================================================

import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('apps')


class NotificationService:
    """Envoi de notifications : base de données + Firebase FCM."""

    @classmethod
    def send(cls, user, notif_type: str, title: str, message: str, ticket=None,
             sms_text=None, sms_kind=None):
        """
        Notification en base + push FCM. Si `sms_text` est fourni, un SMS est aussi envoyé
        (sauf préférence contraire de l'usager) ; son échec n'empêche jamais le reste.
        """
        from .models import Notification
        notif = Notification.objects.create(
            user=user, type=notif_type,
            title=title, message=message, ticket=ticket,
        )
        cls._send_fcm(user, title, message, notif)
        if sms_text:
            from .sms import SMSService
            try:
                SMSService.send_to_user(user, sms_text, kind=sms_kind, ticket=ticket)
            except Exception:
                logger.exception("[SMS] Erreur lors de l'envoi du SMS")
        return notif

    @classmethod
    def notify_queue_progress(cls, queue):
        """
        À appeler quand une file avance (appel, annulation, service) : prévient, une seule fois
        par ticket, les usagers dont il ne reste plus que SMS_APPROACH_THRESHOLD personnes
        (ou moins) devant eux — notification dans l'app + SMS.
        """
        from apps.tickets.models import Ticket
        threshold = max(0, settings.SMS_APPROACH_THRESHOLD)
        try:
            waiting = list(
                Ticket.objects.filter(queue=queue, status=Ticket.STATUS_WAITING)
                .select_related('user', 'queue__service')
                .order_by('-priority_score', 'requested_at')[:threshold + 1]
            )
            for ahead, ticket in enumerate(waiting):
                if ticket.approach_notified_at:
                    continue
                # Réservation atomique : deux appels simultanés ne préviennent pas deux fois
                claimed = Ticket.objects.filter(
                    pk=ticket.pk, approach_notified_at__isnull=True,
                ).update(approach_notified_at=timezone.now())
                if not claimed:
                    continue
                service = ticket.queue.service.name
                if ahead == 0:
                    detail = 'vous etes le prochain'
                    detail_app = 'Vous êtes le prochain'
                else:
                    detail = f'plus que {ahead} personne(s) avant vous'
                    detail_app = f'Plus que {ahead} personne(s) avant vous'
                cls.send(
                    user=ticket.user, notif_type='reminder',
                    title='⏳ Votre tour approche',
                    message=f'Ticket n°{ticket.number} — {detail_app} ({service}). '
                            f'Rendez-vous bientôt au guichet.',
                    ticket=ticket,
                    sms_kind='approach',
                    sms_text=f'MonTour : votre tour approche. Ticket numero {ticket.number} ({service}), '
                             f'{detail}. Rendez-vous bientot au guichet.',
                )
        except Exception:
            logger.exception('[SMS] Erreur lors du rappel de fin de file')

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