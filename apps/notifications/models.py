# =============================================================
# MonTour — apps/notifications/models.py
# =============================================================

import uuid
from django.db import models
from apps.accounts.models import User


class Notification(models.Model):
    TYPE_TICKET_TAKEN = 'ticket_taken'
    TYPE_YOUR_TURN    = 'your_turn'
    TYPE_REMINDER     = 'reminder'
    TYPE_INFO         = 'info'
    TYPE_WARNING      = 'warning'
    TYPE_CHOICES = [
        (TYPE_TICKET_TAKEN, 'Ticket réservé'),
        (TYPE_YOUR_TURN,    'Votre tour'),
        (TYPE_REMINDER,     'Rappel'),
        (TYPE_INFO,         'Information'),
        (TYPE_WARNING,      'Avertissement'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    ticket     = models.ForeignKey(
        'tickets.Ticket', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table    = 'mt_notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering    = ['-created_at']
        indexes     = [models.Index(fields=['user', 'is_read'])]

    def __str__(self):
        return f'[{self.type}] {self.title} → {self.user.username}'

    def mark_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class SMSLog(models.Model):
    """Journal des SMS : suivi des envois, des échecs et du coût."""
    KIND_APPROACH = 'approach'
    KIND_CALLED   = 'called'
    KIND_TEST     = 'test'
    KIND_CHOICES = [
        (KIND_APPROACH, 'Tour qui approche'),
        (KIND_CALLED,   'Tour arrivé'),
        (KIND_TEST,     'Test'),
    ]
    STATUS_SENT    = 'sent'
    STATUS_FAILED  = 'failed'
    STATUS_SKIPPED = 'skipped'
    STATUS_CHOICES = [
        (STATUS_SENT,    'Envoyé'),
        (STATUS_FAILED,  'Échec'),
        (STATUS_SKIPPED, 'Ignoré'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='sms_logs')
    ticket     = models.ForeignKey(
        'tickets.Ticket', null=True, blank=True, on_delete=models.SET_NULL, related_name='sms_logs'
    )
    kind       = models.CharField(max_length=10, choices=KIND_CHOICES)
    to         = models.CharField(max_length=20, blank=True)
    text       = models.TextField(blank=True)
    provider   = models.CharField(max_length=20, blank=True)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES)
    provider_message_id = models.CharField(max_length=100, blank=True)
    error      = models.TextField(blank=True, help_text="Motif de l'échec ou de l'abandon")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mt_sms_logs'
        verbose_name = 'SMS'
        verbose_name_plural = 'SMS'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'created_at'])]

    def __str__(self):
        return f'[{self.kind}/{self.status}] {self.to}'
