# =============================================================
# MonTour — apps/chatbot/models.py
# =============================================================

import uuid
from django.db import models
from apps.accounts.models import User


class ChatMessage(models.Model):
    ROLE_USER = 'user'
    ROLE_BOT  = 'bot'
    ROLE_CHOICES = [(ROLE_USER, 'Utilisateur'), (ROLE_BOT, 'Bot')]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content    = models.TextField()
    role       = models.CharField(max_length=5, choices=ROLE_CHOICES, default=ROLE_USER)
    intent     = models.CharField(max_length=50, blank=True, help_text='Intention Rasa détectée')
    confidence = models.FloatField(default=0.0, help_text='Score de confiance Rasa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mt_chat_messages'
        verbose_name = 'Message chatbot'
        verbose_name_plural = 'Messages chatbot'
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.role}] {self.user.username}: {self.content[:50]}'