# =============================================================
# MonTour — apps/stats/models.py
# Modèle DailyReport : rapport journalier pré-calculé (cache stats)
# =============================================================

from django.db import models
from apps.services.models import Service


class DailyReport(models.Model):
    """Snapshot quotidien des statistiques par service."""
    service        = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='daily_reports')
    date           = models.DateField()
    total_tickets  = models.PositiveIntegerField(default=0)
    served         = models.PositiveIntegerField(default=0)
    cancelled      = models.PositiveIntegerField(default=0)
    avg_wait       = models.FloatField(default=0.0, help_text='Temps moyen d\'attente en minutes')
    peak_hour      = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_rating     = models.FloatField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'mt_daily_reports'
        unique_together = ['service', 'date']
        ordering        = ['-date']

    def __str__(self):
        return f'Rapport {self.date} — {self.service.name}'