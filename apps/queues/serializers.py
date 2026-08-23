# =============================================================
# MonTour — apps/queues/serializers.py
# =============================================================

from rest_framework import serializers
from apps.tickets.models import Ticket
from .models import Queue


class QueueTicketPreviewSerializer(serializers.ModelSerializer):
    """Aperçu léger d'un ticket dans la liste de file."""
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = Ticket
        fields = ['id', 'number', 'priority', 'priority_score', 'estimated_wait', 'user_name', 'requested_at']


class QueueSerializer(serializers.ModelSerializer):
    service_name  = serializers.CharField(source='service.name', read_only=True)
    service_icon  = serializers.CharField(source='service.icon', read_only=True)
    service_color = serializers.CharField(source='service.color', read_only=True)
    waiting_count = serializers.ReadOnlyField()
    tickets       = serializers.SerializerMethodField()

    class Meta:
        model  = Queue
        fields = [
            'id', 'service_name', 'service_icon', 'service_color',
            'status', 'current_number', 'called_number',
            'max_capacity', 'waiting_count', 'tickets',
            'opened_at', 'closed_at',
        ]

    def get_tickets(self, obj):
        waiting = obj.tickets.filter(status='waiting').order_by('-priority_score', 'requested_at')
        return QueueTicketPreviewSerializer(waiting[:20], many=True).data