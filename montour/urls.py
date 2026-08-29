# =============================================================
# MonTour — montour/urls.py
# Configuration des URLs principales (routeur racine)
# =============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from montour.pwa_views import manifest, service_worker

urlpatterns = [
    # ── Application Web Frontend ───────────────────────────────
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # ── PWA (manifest, service worker) ─────────────────────────
    path('manifest.json', manifest, name='pwa-manifest'),
    path('sw.js', service_worker, name='pwa-service-worker'),

    # ── Administration Django ──────────────────────────────────
    path('admin/', admin.site.urls),

    # ── API v1 ─────────────────────────────────────────────────
    path('api/v1/auth/',          include('apps.accounts.urls',      namespace='accounts')),
    path('api/v1/services/',      include('apps.services.urls',      namespace='services')),
    path('api/v1/queues/',        include('apps.queues.urls',        namespace='queues')),
    path('api/v1/tickets/',       include('apps.tickets.urls',       namespace='tickets')),
    path('api/v1/notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('api/v1/chatbot/',       include('apps.chatbot.urls',       namespace='chatbot')),
    path('api/v1/stats/',         include('apps.stats.urls',         namespace='stats')),

    # ── JWT Token Refresh ──────────────────────────────────────
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Documentation OpenAPI / Swagger ───────────────────────
    path('api/schema/',           SpectacularAPIView.as_view(),            name='schema'),
    path('api/docs/',             SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',            SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),

    # ── Health check ───────────────────────────────────────────
    path('api/health/', include('montour.health_urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)