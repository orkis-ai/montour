# =============================================================
# MonTour — apps/accounts/signals.py
# Signaux Django : actions automatiques post-sauvegarde
# =============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_user_queue(sender, instance, created, **kwargs):
    """
    À la création d'un utilisateur :
    - Initialise son cache de notifications
    - Log la création (optionnel)
    """
    if created:
        import logging
        logger = logging.getLogger('apps')
        logger.info(f'[Signal] Nouvel utilisateur créé : {instance.username} ({instance.email})')