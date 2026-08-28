# =============================================================
# MonTour — apps/services/views.py
# =============================================================

from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Service
from .serializers import ServiceSerializer, ServiceCreateUpdateSerializer
from montour.utils import api_response, api_error
from montour.permissions import IsAdminUser


class ServiceListView(generics.ListAPIView):
    """GET /api/v1/services/ — Liste tous les services actifs."""
    serializer_class    = ServiceSerializer
    permission_classes  = [permissions.IsAuthenticated]
    filter_backends     = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields    = ['category', 'is_active']
    search_fields       = ['name', 'description']

    def get_queryset(self):
        return Service.objects.filter(is_active=True).prefetch_related('hours', 'queue')


class ServiceDetailView(generics.RetrieveAPIView):
    """GET /api/v1/services/<id>/ — Détail d'un service."""
    serializer_class   = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = Service.objects.all()


class ServiceCreateView(generics.CreateAPIView):
    """POST /api/v1/services/create/ — Créer un service (Admin)."""
    serializer_class   = ServiceCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        service = serializer.save()
        from apps.queues.models import Queue
        Queue.objects.create(service=service)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_response(data=serializer.data, message='Service créé avec succès.', status_code=201)


class ServiceUpdateView(generics.UpdateAPIView):
    """PUT/PATCH /api/v1/services/<id>/update/ — Modifier un service (Admin)."""
    serializer_class   = ServiceCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset           = Service.objects.all()


class ServiceDeleteView(generics.DestroyAPIView):
    """DELETE /api/v1/services/<id>/delete/ — Désactiver un service (Admin)."""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset           = Service.objects.all()

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        service.is_active = False
        service.save(update_fields=['is_active'])
        return api_response(message='Service désactivé avec succès.')