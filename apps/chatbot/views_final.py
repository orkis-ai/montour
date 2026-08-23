# =============================================================
# MonTour — apps/chatbot/views.py
# =============================================================

import requests
import logging
from django.conf import settings
from rest_framework import permissions
from rest_framework.views import APIView

from montour.utils import api_response, api_error
from .models import ChatMessage
from .serializers import ChatMessageSerializer, ChatInputSerializer

logger = logging.getLogger('apps')

KNOWLEDGE_BASE = {
    'bonjour':      'Bonjour ! Je suis l\'assistant MonTour 🤖. Je peux vous aider avec votre ticket, le temps d\'attente ou les services disponibles.',
    'ticket':       'Pour réserver un ticket 🎫, allez dans **File d\'attente**, choisissez un service et appuyez sur **Prendre un ticket**.',
    'attente':      'Le temps d\'attente ⏱️ est estimé par notre IA en analysant l\'affluence, l\'heure et votre niveau de priorité.',
    'annuler':      'Pour annuler, allez dans **Mes Tickets** et appuyez sur **Annuler**. Cela libère votre place dans la file.',
    'priorité':     'Les niveaux : Urgent 🚨, Handicap ♿, Senior 👴, Normal 👤. Modifiez votre profil pour changer.',
    'notification': 'Activez les notifications 🔔 pour être alerté quand votre tour approche.',
    'horaire':      'Les services sont ouverts de 8h à 17h 🕗, du lundi au vendredi.',
    'service':      'MonTour propose : Centre de Santé 🏥, Guichet Administratif 🏛️, Agence PEBCO 🏦, ATDA Pôle 4 🌾.',
    'aide':         'Je réponds sur : ticket, attente, annuler, priorité, notification, horaire, service.',
}


class ChatbotView(APIView):
    """POST /api/v1/chatbot/message/ — Envoyer un message au chatbot."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Message invalide.', details=serializer.errors)

        message = serializer.validated_data['message']

        # Sauvegarder message utilisateur
        ChatMessage.objects.create(user=request.user, content=message, role='user')

        # Obtenir réponse
        response_text, intent, confidence = self._get_response(message, request.user)

        # Sauvegarder réponse bot
        bot_msg = ChatMessage.objects.create(
            user=request.user, content=response_text,
            role='bot', intent=intent, confidence=confidence,
        )

        return api_response(data={
            'message':    response_text,
            'message_id': str(bot_msg.id),
            'intent':     intent,
        })

    def _get_response(self, message: str, user):
        """Essaie Rasa d'abord, puis repli local."""
        rasa_url = settings.MONTOUR_AI.get('RASA_API_URL', '')
        if rasa_url:
            try:
                resp = requests.post(
                    f'{rasa_url}/webhooks/rest/webhook',
                    json={'sender': str(user.id), 'message': message},
                    timeout=3,
                )
                if resp.status_code == 200 and resp.json():
                    data = resp.json()
                    text = ' '.join(d.get('text', '') for d in data if d.get('text'))
                    if text:
                        return text, 'rasa', 1.0
            except requests.RequestException as e:
                logger.warning(f'[Rasa] Indisponible: {e}')

        # Réponse locale
        lower = message.lower()
        for key, val in KNOWLEDGE_BASE.items():
            if key in lower:
                return val, key, 0.9
        return (
            'Je n\'ai pas bien compris. Essayez : ticket, attente, annuler, priorité, service ou aide.',
            'unknown', 0.0
        )


class ChatHistoryView(APIView):
    """GET /api/v1/chatbot/history/ — Historique des 50 derniers messages."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        messages = (ChatMessage.objects.filter(user=request.user)
                    .order_by('created_at')[:50])
        return api_response(data=ChatMessageSerializer(messages, many=True).data)


class ClearChatView(APIView):
    """DELETE /api/v1/chatbot/clear/ — Effacer l'historique du chatbot."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        count, _ = ChatMessage.objects.filter(user=request.user).delete()
        return api_response(message=f'{count} message(s) supprimé(s).')