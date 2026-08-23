# =============================================================
# MonTour — apps/tickets/models.py
# Modèle principal : Ticket (jeton virtuel de file d'attente)
# =============================================================

import uuid
from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.queues.models import Queue


class Ticket(models.Model):
    """
    Ticket virtuel représentant la position d'un usager dans une file.
    Cycle de vie : waiting → called → served | cancelled
    """

    STATUS_WAITING   = 'waiting'
    STATUS_CALLED    = 'called'
    STATUS_SERVED    = 'served'
    STATUS_CANCELLED = 'cancelled'
    STATUS_MISSED    = 'missed'     # Usager absent lors de l'appel
    STATUS_CHOICES = [
        (STATUS_WAITING,   'En attente'),
        (STATUS_CALLED,    'Appelé'),
        (STATUS_SERVED,    'Servi'),
        (STATUS_CANCELLED, 'Annulé'),
        (STATUS_MISSED,    'Absent'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue           = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='tickets')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')

    # Numéro de passage
    number          = models.PositiveIntegerField(help_text='Numéro attribué dans la file')

    # Statut
    status          = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_WAITING)

    # Priorité au moment de la réservation (copie de user.priority)
    priority        = models.CharField(
        max_length=10,
        choices=User.PRIORITY_CHOICES,
        default=User.PRIORITY_NORMAL,
    )
    priority_score  = models.PositiveIntegerField(default=0, help_text='Score calculé par l\'IA pour trier la file')

    # Prédiction IA
    estimated_wait  = models.PositiveIntegerField(default=0, help_text='Temps d\'attente estimé en minutes (IA)')

    # Horodatages du cycle de vie
    requested_at    = models.DateTimeField(default=timezone.now)
    called_at       = models.DateTimeField(null=True, blank=True)
    served_at       = models.DateTimeField(null=True, blank=True)
    cancelled_at    = models.DateTimeField(null=True, blank=True)

    # Durée réelle d'attente (calculée à la clôture)
    actual_wait     = models.PositiveIntegerField(null=True, blank=True, help_text='Durée réelle en minutes')

    # Note de satisfaction (optionnelle, post-service)
    rating          = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    feedback        = models.TextField(blank=True)

    class Meta:
        db_table    = 'mt_tickets'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering    = ['-priority_score', 'requested_at']
        indexes = [
            models.Index(fields=['queue', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'requested_at']),
        ]

    def __str__(self):
        return f'Ticket #{self.number} — {self.queue.service.name} [{self.status}]'

    @property
    def is_active(self):
        """Vrai si le ticket est en attente ou actuellement appelé au guichet."""
        return self.status in [self.STATUS_WAITING, self.STATUS_CALLED]

    @property
    def wait_time_minutes(self):
        """Calcule le temps d'attente réel en minutes."""
        if self.called_at and self.requested_at:
            delta = self.called_at - self.requested_at
            return int(delta.total_seconds() / 60)
        return None

    def call(self):
        """Passe le ticket à l'état 'appelé'."""
        self.status    = self.STATUS_CALLED
        self.called_at = timezone.now()
        self.queue.called_number = self.number
        self.queue.save(update_fields=['called_number'])
        self.save(update_fields=['status', 'called_at'])

    def serve(self):
        """Clôture le ticket comme 'servi'."""
        self.status    = self.STATUS_SERVED
        self.served_at = timezone.now()
        if self.called_at:
            delta = self.served_at - self.requested_at
            self.actual_wait = int(delta.total_seconds() / 60)
        self.save(update_fields=['status', 'served_at', 'actual_wait'])

    def cancel(self):
        """Annule le ticket."""
        self.status       = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at'])

    def mark_missed(self):
        """Marque l'usager comme absent."""
        self.status    = self.STATUS_MISSED
        self.served_at = timezone.now()
        self.save(update_fields=['status', 'served_at'])