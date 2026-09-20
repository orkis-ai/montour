# =============================================================
# MonTour — apps/queues/serializers.py
# =============================================================

from rest_framework import serializers
from apps.tickets.models import Ticket
from .models import Queue


class QueueTicketPreviewSerializer(serializers.ModelSerializer):
    """Aperçu léger d'un ticket dans la liste de file."""
    user_name = serializers.SerializerMethodField()
    is_mine   = serializers.SerializerMethodField()

    class Meta:
        model  = Ticket
        fields = ['id', 'number', 'priority', 'priority_score', 'estimated_wait',
                  'user_name', 'is_mine', 'requested_at']

    def _user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def get_is_mine(self, obj):
        user = self._user()
        return bool(user and user.is_authenticated and obj.user_id == user.id)

    def get_user_name(self, obj):
        # Vie privée : un usager ne voit pas le nom des autres personnes en file
        # (seuls les agents/admin et le propriétaire du ticket voient le nom).
        user = self._user()
        if user and user.is_authenticated and (obj.user_id == user.id or user.role in ('agent', 'admin')):
            return obj.user.username
        return 'Usager'


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
        return QueueTicketPreviewSerializer(waiting.select_related('user')[:20], many=True, context=self.context).data