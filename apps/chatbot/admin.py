# =============================================================
# MonTour — apps/chatbot/admin.py
# =============================================================

from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ['user', 'role', 'content_preview', 'intent', 'confidence', 'created_at']
    list_filter   = ['role', 'intent']
    search_fields = ['user__username', 'content', 'intent']
    ordering      = ['-created_at']

    @admin.display(description='Message')
    def content_preview(self, obj):
        return obj.content[:60]
