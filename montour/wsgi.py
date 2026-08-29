# =============================================================
# MonTour — montour/wsgi.py
# Point d'entrée WSGI (Gunicorn, uWSGI, Vercel Serverless)
# =============================================================

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'montour.settings')

# Vercel n'a pas d'étape de build/release pour ce projet (pas de buildCommand
# dans vercel.json) : sans ceci, la base Postgres de prod ne reçoit jamais les
# migrations et WhiteNoise n'a aucun fichier statique collecté (admin, Swagger
# UI cassés). On le fait donc une fois par démarrage à froid de la fonction.
# Idempotent et peu coûteux : migrate/collectstatic ne font rien s'il n'y a
# rien de nouveau à appliquer.
if os.getenv('VERCEL'):
    django.setup()
    from django.core.management import call_command

    try:
        call_command('migrate', interactive=False, verbosity=0)
    except Exception:
        pass

    try:
        call_command('collectstatic', interactive=False, verbosity=0, clear=True)
    except Exception:
        pass

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
