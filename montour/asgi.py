# =============================================================
# MonTour — montour/asgi.py
# Point d'entrée ASGI (Daphne, Uvicorn — WebSocket support)
# =============================================================

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'montour.settings')
application = get_asgi_application()

# Pour activer les WebSockets (temps réel), installer django-channels
# et décommenter :
#
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import apps.queues.routing as queue_routing
#
# application = ProtocolTypeRouter({
#     "http":      get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(queue_routing.websocket_urlpatterns)
#     ),
# })