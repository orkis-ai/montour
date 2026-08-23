# =============================================================
# MonTour — apps/stats/urls.py
# =============================================================

from django.urls import path
from .views import GlobalStatsView, UserStatsView, ServiceStatsView

app_name = 'stats'

urlpatterns = [
    path('',                            GlobalStatsView.as_view(),  name='global'),
    path('me/',                         UserStatsView.as_view(),    name='user'),
    path('services/<uuid:service_id>/', ServiceStatsView.as_view(), name='service'),
]