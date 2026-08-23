# =============================================================
# MonTour — apps/services/admin.py
# =============================================================

from django.contrib import admin
from .models import Service, ServiceHours


class ServiceHoursInline(admin.TabularInline):
    model  = ServiceHours
    extra  = 7
    fields = ['day', 'open_time', 'close_time', 'is_open']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'avg_service_time', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['name']
    inlines       = [ServiceHoursInline]
    list_editable = ['is_active', 'avg_service_time']