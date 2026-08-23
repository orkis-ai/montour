# =============================================================
# MonTour — apps/notifications/serializers.py
# =============================================================

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_icon = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = ['id', 'type', 'type_icon', 'title', 'message',
                  'is_read', 'created_at', 'read_at', 'ticket']
        read_only_fields = ['id', 'created_at', 'read_at']

    def get_type_icon(self, obj):
        icons = {
            'ticket_taken': '🎫',
            'your_turn':    '🔔',
            'reminder':     '⏰',
            'info':         'ℹ️',
            'warning':      '⚠️',
        }
        return icons.get(obj.type, '📢')