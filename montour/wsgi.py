# =============================================================
# MonTour — montour/wsgi.py
# Point d'entrée WSGI (Gunicorn, uWSGI, Vercel Serverless)
# =============================================================

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'montour.settings')
application = get_wsgi_application()
app = application