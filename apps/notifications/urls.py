# =============================================================
# MonTour — apps/notifications/urls.py
# =============================================================

from django.urls import path
from .views import (
    NotificationListView, NotificationReadAllView,
    NotificationReadView, UnreadCountView, NotificationDeleteView,
)

app_name = 'notifications'

urlpatterns = [
    path('',                        NotificationListView.as_view(),   name='list'),
    path('read-all/',               NotificationReadAllView.as_view(), name='read-all'),
    path('unread-count/',           UnreadCountView.as_view(),         name='unread-count'),
    path('<uuid:notif_id>/read/',   NotificationReadView.as_view(),    name='read'),
    path('<uuid:notif_id>/delete/', NotificationDeleteView.as_view(),  name='delete'),
]