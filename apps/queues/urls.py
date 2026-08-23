# =============================================================
# MonTour — apps/queues/urls.py
# =============================================================

from django.urls import path
from .views import QueueListView, QueueDetailView, QueueToggleView, QueueResetView

app_name = 'queues'

urlpatterns = [
    path('',                           QueueListView.as_view(),   name='list'),
    path('<uuid:service_id>/',         QueueDetailView.as_view(), name='detail'),
    path('<uuid:queue_id>/toggle/',    QueueToggleView.as_view(), name='toggle'),
    path('<uuid:queue_id>/reset/',     QueueResetView.as_view(),  name='reset'),
]