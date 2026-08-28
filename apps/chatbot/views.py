# =============================================================
# MonTour — apps/chatbot/views.py
# Chatbot : pont vers Rasa ou réponses locales de secours
# =============================================================

import requests
import logging
from django.conf import settings
from rest_framework import permissions
from rest_framework.views import APIView
from montour.utils import api_response, api_error
from montour.validators import sanitize_text
from .models import ChatMessage
from .serializers import ChatMessageSerializer, ChatInputSerializer

logger = logging.getLogger('apps')

# Base de connaissances locale (fallback si Rasa est indisponible)
KNOWLEDGE_BASE = {
    'bonjour':       'Bonjour ! Je suis l\'assistant MonTour 🤖. Je peux vous aider avec votre ticket, le temps d\'attente ou les services disponibles.',
    'ticket':        'Pour réserver un ticket, allez dans **File d\'attente**, choisissez un service et appuyez sur **Prendre un ticket**. Vous recevrez une confirmation avec votre numéro.',
    'attente':       'Le temps d\'attente est estimé par notre IA en analysant l\'affluence actuelle, l\'heure de la journée et votre niveau de priorité.',
    'annuler':       'Pour annuler votre ticket, allez dans **Mes Tickets** et appuyez sur **Annuler**. Cela libère votre place dans la file.',
    'priorité':      'Les niveaux de priorité disponibles : Urgent (urgence médicale), Handicap, Senior, Normal. Modifiez votre profil pour changer votre priorité.',
    'notification':  'Activez les notifications push pour être alerté quand votre tour approche. Configurez-les dans les paramètres de votre téléphone.',
    'horaire':       'Les services sont généralement ouverts de 8h à 17h, du lundi au vendredi. Vérifiez chaque service pour ses horaires exacts.',
    'service':       'MonTour propose 4 services : Centre de Santé 🏥, Guichet Administratif 🏛️, Agence PEBCO 🏦, et ATDA Pôle 4 🌾.',
    'aide':          'Voici ce que je peux faire : ticket, attente, annuler, priorité, notification, horaire, service. Tapez un mot-clé pour commencer.',
}


class ChatbotView(APIView):
    """
    POST /api/v1/chatbot/message/
    Envoie un message au chatbot (Rasa ou local).
    Body: { "message": "comment prendre un ticket ?" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Message invalide', details=serializer.errors)

        raw_message = serializer.validated_data['message']
        clean_message = sanitize_text(raw_message, max_length=1000)

        ChatMessage.objects.create(
            user=request.user, content=clean_message, role='user'
        )

        response_text = self._get_response(clean_message, request.user)

        bot_msg = ChatMessage.objects.create(
            user=request.user, content=response_text, role='bot'
        )

        return api_response(data={
            'message': response_text,
            'message_id': str(bot_msg.id),
        })

    def _get_response(self, message: str, user) -> str:
        """Essaie Rasa, sinon repli sur la base locale."""
        rasa_url = settings.MONTOUR_AI.get('RASA_API_URL')
        if rasa_url:
            try:
                resp = requests.post(
                    f'{rasa_url}/webhooks/rest/webhook',
                    json={'sender': str(user.id), 'message': message},
                    timeout=3,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return ' '.join(d.get('text', '') for d in data)
            except requests.RequestException as e:
                logger.warning(f'[Rasa] Indisponible: {e}')

        # Réponse locale
        lower = message.lower()
        for key, val in KNOWLEDGE_BASE.items():
            if key in lower:
                return val
        return ('Je n\'ai pas bien compris votre question. '
                'Essayez : ticket, attente, annuler, priorité, notification ou service.')


class ChatHistoryView(APIView):
    """GET /api/v1/chatbot/history/ — Historique des messages du chatbot (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # RLS: un utilisateur ne peut voir que son historique
        messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')[:50]
        return api_response(data=ChatMessageSerializer(messages, many=True).data)


class ClearChatView(APIView):
    """DELETE /api/v1/chatbot/clear/ — Effacer l'historique de discussion (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        # RLS: un utilisateur n'efface que son historique
        ChatMessage.objects.filter(user=request.user).delete()
        return api_response(message='Historique effacé avec succès.')