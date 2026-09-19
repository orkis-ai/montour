# =============================================================
# MonTour — montour/health_urls.py
# =============================================================

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.utils import timezone


def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    # Sur Vercel, SQLite vit dans /tmp : les données sont perdues à chaque redémarrage
    persistent = db_ok and not (
        settings.IS_VERCEL and settings.DATABASES['default']['ENGINE'].endswith('sqlite3')
    )
    return JsonResponse({
        'status': 'ok' if persistent else 'degraded',
        'app': 'MonTour API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'database': 'connected' if db_ok else 'error',
        'persistent_storage': persistent,
    })


urlpatterns = [
    path('', health_check, name='health'),
]