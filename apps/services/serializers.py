# =============================================================
# MonTour — apps/services/serializers.py
# =============================================================

from rest_framework import serializers
from .models import Service, ServiceHours


class ServiceHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model  = ServiceHours
        fields = ['day', 'day_name', 'open_time', 'close_time', 'is_open']


class ServiceSerializer(serializers.ModelSerializer):
    hours        = ServiceHoursSerializer(many=True, read_only=True)
    queue_length = serializers.SerializerMethodField()
    queue_status = serializers.SerializerMethodField()
    current_number = serializers.SerializerMethodField()

    class Meta:
        model  = Service
        fields = [
            'id', 'name', 'description', 'category', 'icon', 'color',
            'avg_service_time', 'address', 'phone', 'is_active',
            'hours', 'queue_length', 'queue_status', 'current_number',
        ]

    def get_queue_length(self, obj):
        from apps.queues.models import Queue
        try:
            return obj.queue.tickets.filter(status='waiting').count()
        except Exception:
            return 0

    def get_queue_status(self, obj):
        from apps.queues.models import Queue
        try:
            return obj.queue.status
        except Exception:
            return 'closed'

    def get_current_number(self, obj):
        from apps.queues.models import Queue
        try:
            return obj.queue.called_number
        except Exception:
            return 0


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Service
        fields = ['name', 'description', 'category', 'icon', 'color', 'avg_service_time', 'address', 'phone']