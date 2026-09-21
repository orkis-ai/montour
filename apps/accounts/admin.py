# =============================================================
# MonTour — apps/accounts/admin.py
# =============================================================

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, FCMToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'email', 'role', 'priority', 'is_active', 'date_joined']
    list_filter   = ['role', 'priority', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering      = ['-date_joined']

    fieldsets = (
        ('Identité',    {'fields': ('username', 'email', 'phone', 'avatar')}),
        ('Rôle & Priorité', {'fields': ('role', 'priority')}),
        ('Sécurité',    {'fields': ('password',)}),
        ('Firebase',    {'fields': ('firebase_uid',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',       {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'role', 'priority', 'password1', 'password2'),
        }),
    )
    readonly_fields = ['date_joined', 'last_login']

    actions = ['send_test_sms']

    @admin.action(description='Envoyer un SMS de test aux utilisateurs sélectionnés')
    def send_test_sms(self, request, queryset):
        """Vérifie la configuration eSMS Africa en production (résultat aussi visible dans SMS)."""
        from apps.notifications.models import SMSLog
        from apps.notifications.sms import SMSService
        for user in queryset:
            entry = SMSService.send_to_user(
                user, 'MonTour : SMS de test, la configuration des rappels fonctionne.',
                kind=SMSLog.KIND_TEST,
            )
            level = messages.SUCCESS if entry.status == SMSLog.STATUS_SENT else messages.WARNING
            self.message_user(
                request,
                f"{user.username} : {entry.get_status_display()}"
                + (f" — {entry.error}" if entry.error else f" ({entry.to})"),
                level,
            )


@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display  = ['user', 'device_type', 'is_active', 'created_at']
    list_filter   = ['device_type', 'is_active']
    search_fields = ['user__email', 'user__username']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ['user', 'expires_at', 'used', 'created_at']
    list_filter   = ['used']
    search_fields = ['user__email']