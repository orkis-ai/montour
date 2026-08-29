# =============================================================
# MonTour — montour/pwa_views.py
# Sert manifest.json et sw.js à la racine du site (requis pour l'installation
# PWA et la portée du service worker), en s'appuyant sur les finders
# staticfiles Django plutôt que sur un dossier séparé non garanti d'être
# inclus dans le bundle de la fonction serverless (cf. l'ancien public/,
# introuvable en prod alors que /static/... fonctionne).
# =============================================================

from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseNotFound


def _read_static(relative_path):
    path = finders.find(relative_path)
    if not path:
        return None
    with open(path, 'rb') as f:
        return f.read()


def manifest(request):
    content = _read_static('pwa/manifest.json')
    if content is None:
        return HttpResponseNotFound()
    return HttpResponse(content, content_type='application/manifest+json')


def service_worker(request):
    content = _read_static('pwa/sw.js')
    if content is None:
        return HttpResponseNotFound()
    response = HttpResponse(content, content_type='text/javascript')
    # Autorise le service worker à contrôler tout le site ("/") même si le
    # fichier est physiquement servi depuis une URL qui n'est pas la racine.
    response['Service-Worker-Allowed'] = '/'
    return response
