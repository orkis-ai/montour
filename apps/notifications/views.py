# =============================================================
# MonTour — apps/notifications/views.py
# =============================================================

from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.views import APIView

from montour.utils import api_response, api_error
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/v1/notifications/ — Notifications de l'utilisateur connecté (RLS)."""
    serializer_class   = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # RLS: filtre systématique par utilisateur connecté
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get('unread'):
            qs = qs.filter(is_read=False)
        return qs.order_by('-created_at')


class NotificationReadAllView(APIView):
    """PUT /api/v1/notifications/read-all/ — Marquer toutes comme lues (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return api_response(message=f'{count} notification(s) marquée(s) comme lues.')


class NotificationReadView(APIView):
    """PUT /api/v1/notifications/<id>/read/ — Marquer une seule comme lue (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, notif_id):
        try:
            # RLS: vérification de propriété
            notif = Notification.objects.get(pk=notif_id, user=request.user)
            notif.mark_read()
            return api_response(message='Notification marquée comme lue.')
        except Notification.DoesNotExist:
            return api_error('Notification introuvable.', 404)


class UnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/ — Nombre de non lues (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return api_response(data={'unread_count': count})


class NotificationDeleteView(APIView):
    """DELETE /api/v1/notifications/<id>/delete/ — Supprimer une notification (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, notif_id):
        try:
            # RLS: vérification de propriété
            notif = Notification.objects.get(pk=notif_id, user=request.user)
            notif.delete()
            return api_response(message='Notification supprimée.')
        except Notification.DoesNotExist:
            return api_error('Notification introuvable.', 404)