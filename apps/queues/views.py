# =============================================================
# MonTour — apps/queues/views.py
# =============================================================

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from montour.utils import api_response, api_error
from .models import Queue
from .serializers import QueueSerializer


class QueueDetailView(APIView):
    """GET /api/v1/queues/<service_id>/ — État complet d'une file."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, service_id):
        try:
            queue = Queue.objects.select_related('service').prefetch_related(
                'tickets__user'
            ).get(service__pk=service_id)
        except Queue.DoesNotExist:
            return api_error('File d\'attente introuvable.', 404)
        return api_response(data=QueueSerializer(queue).data)


class QueueListView(ListAPIView):
    """GET /api/v1/queues/ — Toutes les files."""
    serializer_class   = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Queue.objects.select_related('service').prefetch_related('tickets').order_by('service__name')


class QueueToggleView(APIView):
    """POST /api/v1/queues/<queue_id>/toggle/ — Ouvrir/Fermer."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, queue_id):
        if not (request.user.is_admin or request.user.is_agent):
            return api_error('Permission refusée.', 403)
        try:
            queue = Queue.objects.get(pk=queue_id)
        except Queue.DoesNotExist:
            return api_error('File introuvable.', 404)

        if queue.status == Queue.STATUS_OPEN:
            queue.close()
            msg = 'File fermée.'
        else:
            queue.open()
            msg = 'File ouverte.'
        return api_response(data={'status': queue.status}, message=msg)


class QueueResetView(APIView):
    """POST /api/v1/queues/<queue_id>/reset/ — Réinitialiser (Admin)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, queue_id):
        if not request.user.is_admin:
            return api_error('Permission refusée.', 403)
        try:
            queue = Queue.objects.get(pk=queue_id)
        except Queue.DoesNotExist:
            return api_error('File introuvable.', 404)

        queue.tickets.filter(status='waiting').update(status='cancelled')
        queue.current_number = 0
        queue.called_number  = 0
        queue.save(update_fields=['current_number', 'called_number'])
        return api_response(message='File réinitialisée.')