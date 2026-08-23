# =============================================================
# MonTour — apps/queues/admin.py
# =============================================================

from django.contrib import admin
from .models import Queue


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display   = ['service', 'status', 'current_number', 'called_number', 'get_waiting']
    list_filter    = ['status']
    readonly_fields = ['current_number', 'called_number', 'opened_at', 'closed_at']

    @admin.display(description='En attente')
    def get_waiting(self, obj):
        return obj.waiting_count

    actions = ['open_queues', 'close_queues']

    @admin.action(description='Ouvrir les files sélectionnées')
    def open_queues(self, request, queryset):
        for q in queryset:
            q.open()

    @admin.action(description='Fermer les files sélectionnées')
    def close_queues(self, request, queryset):
        for q in queryset:
            q.close()