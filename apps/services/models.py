# =============================================================
# MonTour — apps/services/models.py
# =============================================================

import uuid
from django.db import models


class Service(models.Model):
    """
    Représente un service proposant une file d'attente
    (ex : Centre de Santé, Guichet Administratif).
    """
    CATEGORY_HEALTH     = 'health'
    CATEGORY_ADMIN      = 'admin'
    CATEGORY_FINANCE    = 'finance'
    CATEGORY_AGRICULTURE = 'agriculture'
    CATEGORY_OTHER      = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_HEALTH,      'Santé'),
        (CATEGORY_ADMIN,       'Administration'),
        (CATEGORY_FINANCE,     'Finance / Microfinance'),
        (CATEGORY_AGRICULTURE, 'Agriculture'),
        (CATEGORY_OTHER,       'Autre'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=100, verbose_name='Nom du service')
    description      = models.TextField(blank=True)
    category         = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    icon             = models.CharField(max_length=10, default='🏢', help_text='Emoji représentant le service')
    color            = models.CharField(max_length=7, default='#1a73e8', help_text='Couleur hexadécimale')
    avg_service_time = models.PositiveIntegerField(default=10, help_text='Temps moyen de service en minutes')
    address          = models.TextField(blank=True, verbose_name='Adresse')
    phone            = models.CharField(max_length=20, blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'mt_services'
        verbose_name    = 'Service'
        verbose_name_plural = 'Services'
        ordering        = ['name']
        indexes         = [models.Index(fields=['category', 'is_active'])]

    def __str__(self):
        return self.name


class ServiceHours(models.Model):
    """Horaires d'ouverture d'un service par jour de la semaine."""
    DAYS = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'),
        (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]
    service    = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='hours')
    day        = models.PositiveSmallIntegerField(choices=DAYS)
    open_time  = models.TimeField()
    close_time = models.TimeField()
    is_open    = models.BooleanField(default=True)

    class Meta:
        db_table = 'mt_service_hours'
        unique_together = ['service', 'day']
        ordering = ['day']

    def __str__(self):
        return f'{self.service.name} — {self.get_day_display()}'