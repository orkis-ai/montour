# =============================================================
# MonTour — apps/services/serializers.py
# =============================================================

from rest_framework import serializers
from .models import Service, ServiceHours
from montour.validators import (
    validate_hex_color, validate_emoji_icon,
    validate_positive_integer, sanitize_text,
)


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
        try:
            return obj.queue.tickets.filter(status='waiting').count()
        except Exception:
            return 0

    def get_queue_status(self, obj):
        try:
            return obj.queue.status
        except Exception:
            return 'closed'

    def get_current_number(self, obj):
        try:
            return obj.queue.called_number
        except Exception:
            return 0


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Service
        fields = ['name', 'description', 'category', 'icon', 'color', 'avg_service_time', 'address', 'phone']

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le nom du service est requis.')
        return sanitize_text(value.strip(), max_length=100)

    def validate_description(self, value):
        return sanitize_text(value, max_length=1000)

    def validate_category(self, value):
        valid = [c[0] for c in Service.CATEGORY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f'Catégorie invalide. Choix possibles : {", ".join(valid)}'
            )
        return value

    def validate_color(self, value):
        return validate_hex_color(value)

    def validate_icon(self, value):
        return validate_emoji_icon(value)

    def validate_avg_service_time(self, value):
        return validate_positive_integer(value, 'Temps moyen de service', max_val=240)