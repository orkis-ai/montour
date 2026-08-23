# =============================================================
# MonTour — apps/services/urls.py
# =============================================================

from django.urls import path
from .views import (
    ServiceListView, ServiceDetailView,
    ServiceCreateView, ServiceUpdateView, ServiceDeleteView,
)

app_name = 'services'

urlpatterns = [
    path('',         ServiceListView.as_view(),   name='list'),
    path('create/',  ServiceCreateView.as_view(),  name='create'),
    path('<uuid:pk>/',        ServiceDetailView.as_view(), name='detail'),
    path('<uuid:pk>/update/', ServiceUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', ServiceDeleteView.as_view(), name='delete'),
]
