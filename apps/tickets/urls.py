# =============================================================
# MonTour — apps/tickets/urls.py
# =============================================================

from django.urls import path
from .views import (
    TakeTicketView, MyTicketsView, CancelTicketView,
    CallNextTicketView, ServeTicketView, RateTicketView,
    QueueTicketsView,
)

app_name = 'tickets'

urlpatterns = [
    path('take/<uuid:queue_id>/',                  TakeTicketView.as_view(),     name='take'),
    path('mine/',                                   MyTicketsView.as_view(),      name='mine'),
    path('<uuid:ticket_id>/cancel/',                CancelTicketView.as_view(),   name='cancel'),
    path('<uuid:ticket_id>/serve/',                 ServeTicketView.as_view(),    name='serve'),
    path('<uuid:ticket_id>/rate/',                  RateTicketView.as_view(),     name='rate'),
    path('queues/<uuid:queue_id>/call-next/',       CallNextTicketView.as_view(), name='call-next'),
    path('queues/<uuid:queue_id>/',                 QueueTicketsView.as_view(),   name='queue-tickets'),
]