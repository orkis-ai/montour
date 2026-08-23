# =============================================================
# MonTour — apps/stats/admin.py
# =============================================================

from django.contrib import admin
from .models import DailyReport


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display  = ['service', 'date', 'total_tickets', 'served', 'cancelled', 'avg_wait']
    list_filter   = ['service', 'date']
    ordering      = ['-date']
    readonly_fields = ['created_at']
