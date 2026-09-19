# =============================================================
# MonTour — apps/tickets/views.py
# =============================================================

from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.views import APIView

from apps.queues.models import Queue
from montour.utils import api_response, api_error, WaitTimePredictor, PriorityScorer
from montour.permissions import IsAgentOrAdmin
from apps.notifications.services import NotificationService
from .models import Ticket
from .serializers import TicketSerializer, TicketRatingSerializer


class TakeTicketView(APIView):
    """POST /api/v1/tickets/take/<queue_id>/ — Prendre un ticket."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, queue_id):
        try:
            queue = Queue.objects.select_related('service').get(pk=queue_id)
        except Queue.DoesNotExist:
            return api_error('File d\'attente introuvable.', 404)

        if queue.status != Queue.STATUS_OPEN:
            return api_error('Cette file d\'attente est fermée.')
        if queue.is_full:
            return api_error(f'Capacité maximale atteinte ({queue.max_capacity} tickets).')
        if Ticket.objects.filter(queue=queue, user=request.user, status='waiting').exists():
            return api_error('Vous avez déjà un ticket actif dans cette file.', 409)

        user     = request.user
        number   = queue.next_number()
        priority = user.priority
        score    = PriorityScorer.compute(priority, timezone.now())

        waiting_ahead = Ticket.objects.filter(
            queue=queue, status='waiting', priority_score__gte=score
        ).count() + 1

        estimated = WaitTimePredictor.predict(queue.service, waiting_ahead, priority)

        ticket = Ticket.objects.create(
            queue=queue, user=user, number=number,
            priority=priority, priority_score=score, estimated_wait=estimated,
        )

        NotificationService.send(
            user=user,
            notif_type='ticket_taken',
            title='🎫 Ticket réservé !',
            message=(f'Ticket n°{number} confirmé — {queue.service.name}. '
                     f'Temps estimé : ~{estimated} min.'),
            ticket=ticket,
        )

        return api_response(
            data={'ticket': TicketSerializer(ticket).data, 'position': waiting_ahead},
            message='Ticket obtenu avec succès.',
            status_code=201,
        )


class MyTicketsView(generics.ListAPIView):
    """GET /api/v1/tickets/mine/ — Historique des tickets de l'utilisateur connecté (RLS)."""
    serializer_class   = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # RLS: un utilisateur ne peut voir que ses propres tickets
        qs = Ticket.objects.filter(user=self.request.user).select_related('queue__service')
        s = self.request.query_params.get('status')
        if s:
            valid_statuses = [c[0] for c in Ticket.STATUS_CHOICES]
            if s in valid_statuses:
                qs = qs.filter(status=s)
        return qs.order_by('-requested_at')


class CancelTicketView(APIView):
    """DELETE /api/v1/tickets/<ticket_id>/cancel/ — Annuler son ticket (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, ticket_id):
        try:
            # RLS: vérification que le ticket appartient à request.user
            ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
        except Ticket.DoesNotExist:
            return api_error('Ticket introuvable.', 404)
        if ticket.status != Ticket.STATUS_WAITING:
            return api_error('Seuls les tickets en attente peuvent être annulés.', 400)
        ticket.cancel()
        return api_response(data=TicketSerializer(ticket).data, message='Ticket annulé avec succès.')


class CallNextTicketView(APIView):
    """POST /api/v1/tickets/queues/<queue_id>/call-next/ — Appeler le suivant (Agent/Admin)."""
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    def post(self, request, queue_id):
        try:
            queue = Queue.objects.get(pk=queue_id)
        except Queue.DoesNotExist:
            return api_error('File introuvable.', 404)

        next_ticket = (
            Ticket.objects.filter(queue=queue, status=Ticket.STATUS_WAITING)
            .order_by('-priority_score', 'requested_at')
            .select_related('user')
            .first()
        )
        if not next_ticket:
            return api_error('La file est vide.', 404)

        next_ticket.call()

        NotificationService.send(
            user=next_ticket.user,
            notif_type='your_turn',
            title='🔔 Votre tour approche !',
            message=(f'Ticket n°{next_ticket.number} — Présentez-vous immédiatement '
                     f'au guichet de {queue.service.name}.'),
            ticket=next_ticket,
        )

        # Recalculer les estimations pour les tickets restants
        remaining = list(Ticket.objects.filter(queue=queue, status='waiting')
                         .order_by('-priority_score', 'requested_at'))
        for i, t in enumerate(remaining):
            t.estimated_wait = WaitTimePredictor.predict(queue.service, i + 1, t.priority)
        Ticket.objects.bulk_update(remaining, ['estimated_wait'])

        return api_response(
            data=TicketSerializer(next_ticket).data,
            message=f'Ticket n°{next_ticket.number} appelé.',
        )


class ServeTicketView(APIView):
    """POST /api/v1/tickets/<ticket_id>/serve/ — Marquer comme servi (Agent/Admin)."""
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    def post(self, request, ticket_id):
        try:
            ticket = Ticket.objects.select_related('user', 'queue__service').get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return api_error('Ticket introuvable.', 404)
        if ticket.status not in [Ticket.STATUS_CALLED, Ticket.STATUS_WAITING]:
            return api_error(f'Ticket déjà {ticket.status}.', 400)
        ticket.serve()
        return api_response(data=TicketSerializer(ticket).data, message='Ticket marqué comme servi.')


class RateTicketView(APIView):
    """POST /api/v1/tickets/<ticket_id>/rate/ — Noter son expérience (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ticket_id):
        try:
            # RLS: seul le propriétaire du ticket servi peut le noter
            ticket = Ticket.objects.get(pk=ticket_id, user=request.user, status=Ticket.STATUS_SERVED)
        except Ticket.DoesNotExist:
            return api_error('Ticket introuvable ou non encore servi.', 404)
        serializer = TicketRatingSerializer(ticket, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_error('Données invalides', details=serializer.errors)
        serializer.save()
        return api_response(message='Merci pour votre évaluation !')


class QueueTicketsView(generics.ListAPIView):
    """GET /api/v1/tickets/queues/<queue_id>/ — Tickets d'une file (Agent/Admin)."""
    serializer_class   = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    def get_queryset(self):
        queue_id = self.kwargs['queue_id']
        s = self.request.query_params.get('status', 'waiting')
        valid_statuses = [c[0] for c in Ticket.STATUS_CHOICES]
        if s not in valid_statuses:
            s = 'waiting'
        return (Ticket.objects.filter(queue__pk=queue_id, status=s)
                .select_related('user', 'queue__service')
                .order_by('-priority_score', 'requested_at'))