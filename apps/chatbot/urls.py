# =============================================================
# MonTour — apps/chatbot/urls.py
# =============================================================

from django.urls import path
from .views import ChatbotView, ChatHistoryView, ClearChatView

app_name = 'chatbot'

urlpatterns = [
    path('message/', ChatbotView.as_view(),     name='message'),
    path('history/', ChatHistoryView.as_view(), name='history'),
    path('clear/',   ClearChatView.as_view(),   name='clear'),
]