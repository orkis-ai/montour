# =============================================================
# MonTour — apps/tickets/admin.py
# =============================================================

from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display   = ['number', 'queue', 'user', 'priority', 'status', 'estimated_wait', 'actual_wait', 'requested_at']
    list_filter    = ['status', 'priority', 'queue__service']
    search_fields  = ['user__username', 'user__email', 'number']
    readonly_fields = ['requested_at', 'called_at', 'served_at', 'cancelled_at', 'priority_score']
    ordering       = ['-requested_at']
    date_hierarchy = 'requested_at'

    actions = ['mark_as_served', 'mark_as_cancelled']

    @admin.action(description='Marquer comme servis')
    def mark_as_served(self, request, queryset):
        for ticket in queryset.filter(status__in=['waiting', 'called']):
            ticket.serve()

    @admin.action(description='Annuler les tickets sélectionnés')
    def mark_as_cancelled(self, request, queryset):
        for ticket in queryset.filter(status='waiting'):
            ticket.cancel()