# =============================================================
# MonTour — apps/stats/views.py
# =============================================================

from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework import permissions
from rest_framework.views import APIView

from apps.tickets.models import Ticket
from apps.services.models import Service
from apps.accounts.models import User
from montour.utils import api_response, api_error
from montour.permissions import IsAgentOrAdmin


class GlobalStatsView(APIView):
    """GET /api/v1/stats/ — Tableau de bord statistiques global (Admin/Agent)."""
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    def get(self, request):
        today    = timezone.now().date()
        all_tkts = Ticket.objects.all()

        # ── Résumé global ───────────────────────────────────────
        summary = {
            'total_tickets':    all_tkts.count(),
            'served':           all_tkts.filter(status='served').count(),
            'waiting':          all_tkts.filter(status='waiting').count(),
            'called':           all_tkts.filter(status='called').count(),
            'cancelled':        all_tkts.filter(status='cancelled').count(),
            'today':            all_tkts.filter(requested_at__date=today).count(),
            'total_users':      User.objects.filter(is_active=True).count(),
            'avg_wait_minutes': round(
                all_tkts.filter(status='served', actual_wait__isnull=False)
                        .aggregate(avg=Avg('actual_wait'))['avg'] or 0, 1
            ),
            'avg_rating': round(
                all_tkts.filter(rating__isnull=False)
                        .aggregate(avg=Avg('rating'))['avg'] or 0, 2
            ),
        }

        # ── Par service ─────────────────────────────────────────
        by_service = []
        for svc in Service.objects.filter(is_active=True):
            qs = all_tkts.filter(queue__service=svc)
            by_service.append({
                'service_id':   str(svc.id),
                'service_name': svc.name,
                'service_icon': svc.icon,
                'service_color': svc.color,
                'total':     qs.count(),
                'served':    qs.filter(status='served').count(),
                'waiting':   qs.filter(status='waiting').count(),
                'cancelled': qs.filter(status='cancelled').count(),
                'avg_wait':  round(
                    qs.filter(status='served', actual_wait__isnull=False)
                      .aggregate(avg=Avg('actual_wait'))['avg'] or 0, 1
                ),
            })

        # ── Par priorité ────────────────────────────────────────
        by_priority = [
            {
                'priority': p,
                'count':  all_tkts.filter(priority=p).count(),
                'served': all_tkts.filter(priority=p, status='served').count(),
            }
            for p in ['urgent', 'handicap', 'senior', 'normal']
        ]

        # ── Évolution 7 jours ───────────────────────────────────
        daily_7days = []
        for i in range(7):
            day = today - timedelta(days=6 - i)
            daily_7days.append({
                'date':    str(day),
                'tickets': all_tkts.filter(requested_at__date=day).count(),
                'served':  all_tkts.filter(requested_at__date=day, status='served').count(),
            })

        # ── Heure de pointe (heure avec le plus de tickets) ─────
        from django.db.models.functions import ExtractHour
        peak = (all_tkts.annotate(hour=ExtractHour('requested_at'))
                        .values('hour').annotate(n=Count('id'))
                        .order_by('-n').first())
        peak_hour = peak['hour'] if peak else None

        return api_response(data={
            'summary':    summary,
            'by_service': by_service,
            'by_priority': by_priority,
            'daily_7days': daily_7days,
            'peak_hour':   peak_hour,
        })


class UserStatsView(APIView):
    """GET /api/v1/stats/me/ — Statistiques personnelles de l'utilisateur connecté (RLS)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # RLS: statistiques limitées strictement aux tickets de l'utilisateur
        qs = Ticket.objects.filter(user=request.user)
        return api_response(data={
            'total':     qs.count(),
            'served':    qs.filter(status='served').count(),
            'waiting':   qs.filter(status='waiting').count(),
            'cancelled': qs.filter(status='cancelled').count(),
            'avg_wait':  round(
                qs.filter(status='served', actual_wait__isnull=False)
                  .aggregate(avg=Avg('actual_wait'))['avg'] or 0, 1
            ),
            'avg_rating': round(
                qs.filter(rating__isnull=False)
                  .aggregate(avg=Avg('rating'))['avg'] or 0, 2
            ),
        })


class ServiceStatsView(APIView):
    """GET /api/v1/stats/services/<service_id>/ — Stats détaillées d'un service (Agent/Admin)."""
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    def get(self, request, service_id):
        try:
            svc = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return api_error('Service introuvable.', 404)

        qs    = Ticket.objects.filter(queue__service=svc)
        today = timezone.now().date()

        daily = []
        for i in range(30):
            day = today - timedelta(days=29 - i)
            daily.append({
                'date':   str(day),
                'count':  qs.filter(requested_at__date=day).count(),
                'served': qs.filter(requested_at__date=day, status='served').count(),
            })

        return api_response(data={
            'service': {'id': str(svc.id), 'name': svc.name, 'icon': svc.icon},
            'total':   qs.count(),
            'served':  qs.filter(status='served').count(),
            'cancelled': qs.filter(status='cancelled').count(),
            'avg_wait': round(
                qs.filter(status='served', actual_wait__isnull=False)
                  .aggregate(avg=Avg('actual_wait'))['avg'] or 0, 1
            ),
            'daily_30days': daily,
        })