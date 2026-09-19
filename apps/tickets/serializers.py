# =============================================================
# MonTour — apps/tickets/serializers.py
# =============================================================

from rest_framework import serializers
from .models import Ticket
from montour.validators import sanitize_text


class TicketSerializer(serializers.ModelSerializer):
    service_name  = serializers.CharField(source='queue.service.name', read_only=True)
    service_icon  = serializers.CharField(source='queue.service.icon', read_only=True)
    service_color = serializers.CharField(source='queue.service.color', read_only=True)
    user_name     = serializers.CharField(source='user.username', read_only=True)
    position      = serializers.SerializerMethodField()

    class Meta:
        model  = Ticket
        fields = [
            'id', 'number', 'status', 'priority', 'priority_score',
            'estimated_wait', 'actual_wait', 'position',
            'service_name', 'service_icon', 'service_color', 'user_name',
            'requested_at', 'called_at', 'served_at', 'cancelled_at',
            'rating', 'feedback',
        ]
        read_only_fields = [
            'id', 'number', 'priority_score', 'estimated_wait',
            'actual_wait', 'position', 'requested_at', 'called_at',
            'served_at', 'cancelled_at',
        ]

    def get_position(self, obj):
        if obj.status != 'waiting':
            return None
        return Ticket.objects.filter(
            queue=obj.queue,
            status='waiting',
            priority_score__gt=obj.priority_score,
        ).count() + 1


class TicketRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Ticket
        fields = ['rating', 'feedback']

    def validate_rating(self, value):
        if not isinstance(value, int) or not (1 <= value <= 5):
            raise serializers.ValidationError('La note doit être un nombre entier entre 1 et 5.')
        return value

    def validate_feedback(self, value):
        return sanitize_text(value, max_length=1000)