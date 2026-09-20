# =============================================================
# MonTour — apps/notifications/admin.py
# =============================================================

from django.contrib import admin
from .models import Notification, SMSLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter   = ['type', 'is_read']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    ordering      = ['-created_at']

    actions = ['mark_as_read']

    @admin.action(description='Marquer comme lues')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    """Journal en lecture seule : suivi des envois, échecs et abandons."""
    list_display    = ['created_at', 'kind', 'status', 'to', 'provider', 'user']
    list_filter     = ['status', 'kind', 'provider']
    search_fields   = ['to', 'user__username', 'user__email', 'error']
    readonly_fields = [f.name for f in SMSLog._meta.fields]
    ordering        = ['-created_at']

    def has_add_permission(self, request):
        return False
