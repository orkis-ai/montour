# =============================================================
# MonTour — apps/chatbot/serializers.py
# =============================================================

from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ChatMessage
        fields = ['id', 'content', 'role', 'intent', 'confidence', 'created_at']
        read_only_fields = ['id', 'role', 'intent', 'confidence', 'created_at']


class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, allow_blank=False)