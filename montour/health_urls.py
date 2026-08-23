# =============================================================
# MonTour — montour/health_urls.py
# =============================================================

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({
        'status': 'ok' if db_ok else 'degraded',
        'app': 'MonTour API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'database': 'connected' if db_ok else 'error',
    })


urlpatterns = [
    path('', health_check, name='health'),
]