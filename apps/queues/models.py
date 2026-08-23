# =============================================================
# MonTour — apps/queues/models.py
# =============================================================

import uuid
from django.db import models
from apps.services.models import Service


class Queue(models.Model):
    """
    File d'attente associée à un service.
    Relation OneToOne avec Service.
    """
    STATUS_OPEN   = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_OPEN,   'Ouverte'),
        (STATUS_CLOSED, 'Fermée'),
        (STATUS_PAUSED, 'En pause'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service        = models.OneToOneField(Service, on_delete=models.CASCADE, related_name='queue')
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    current_number = models.PositiveIntegerField(default=0, help_text='Dernier numéro attribué')
    called_number  = models.PositiveIntegerField(default=0, help_text='Dernier numéro appelé au guichet')
    max_capacity   = models.PositiveIntegerField(default=100, help_text='Capacité maximale de la file')
    opened_at      = models.DateTimeField(null=True, blank=True)
    closed_at      = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'mt_queues'
        verbose_name = 'File d\'attente'
        verbose_name_plural = 'Files d\'attente'

    def __str__(self):
        return f'Queue — {self.service.name} ({self.status})'

    @property
    def waiting_count(self):
        return self.tickets.filter(status='waiting').count()

    @property
    def is_full(self):
        return self.waiting_count >= self.max_capacity

    def open(self):
        from django.utils import timezone
        self.status    = self.STATUS_OPEN
        self.opened_at = timezone.now()
        self.save(update_fields=['status', 'opened_at'])

    def close(self):
        from django.utils import timezone
        self.status    = self.STATUS_CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])

    def pause(self):
        self.status = self.STATUS_PAUSED
        self.save(update_fields=['status'])

    def next_number(self):
        self.current_number += 1
        self.save(update_fields=['current_number'])
        return self.current_number