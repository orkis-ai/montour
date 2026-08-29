# =============================================================
# MonTour — montour/wsgi.py
# Point d'entrée WSGI (Gunicorn, uWSGI, Vercel Serverless)
# =============================================================

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'montour.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application

# Vercel n'a pas d'étape de build/release pour ce projet : sans ceci, la base
# Postgres de prod ne reçoit jamais les migrations. On le fait donc une fois
# par démarrage à froid de la fonction — migrate ne fait rien s'il n'y a rien
# de nouveau à appliquer. Tout est dans un seul bloc défensif : quoi qu'il
# arrive ici (DB injoignable, timeout, etc.), l'app doit rester utilisable —
# une erreur ici ne doit jamais faire planter toute la fonction serverless.
if os.getenv('VERCEL'):
    try:
        from django.core.management import call_command

        call_command('migrate', interactive=False, verbosity=0)
    except Exception:
        pass
