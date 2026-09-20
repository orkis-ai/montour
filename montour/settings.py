# =============================================================
# MonTour — settings.py
# Configuration principale Django
# =============================================================

import os
import warnings
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Sécurité ────────────────────────────────────────────────
_DEFAULT_SECRET_KEY = 'django-insecure-montour-change-in-prod-2025'
SECRET_KEY = os.getenv('SECRET_KEY', _DEFAULT_SECRET_KEY)

# Vercel : système de fichiers du projet en lecture seule, seul /tmp est
# inscriptible (voir la config des fichiers statiques/media/DB plus bas).
IS_VERCEL = bool(os.getenv('VERCEL'))

# DEBUG actif par défaut en local uniquement : sur Vercel, un oubli de la variable
# d'environnement ne doit pas exposer les pages d'erreur détaillées.
DEBUG = os.getenv('DEBUG', 'False' if IS_VERCEL else 'True') == 'True'

if SECRET_KEY == _DEFAULT_SECRET_KEY and not DEBUG:
    # Pas d'exception : elle ferait tomber tout le site si la variable manque.
    # Mais cette clé est publique (dans le dépôt) : n'importe qui pourrait forger des JWT.
    warnings.warn("SECRET_KEY par défaut utilisée en production : définissez la variable d'environnement SECRET_KEY.")

# URL publique de l'application web. Sert aux liens des emails (vérification, mot de passe
# oublié), à ALLOWED_HOSTS et à CORS : elle ne doit JAMAIS venir de l'en-tête Host de la
# requête (un attaquant pourrait faire envoyer à une victime un lien vers son propre domaine).
# Sur Vercel, le domaine de production est fourni automatiquement.
_vercel_host = os.getenv('VERCEL_PROJECT_PRODUCTION_URL') or os.getenv('VERCEL_URL')
FRONTEND_URL = os.getenv('FRONTEND_URL') or (f'https://{_vercel_host}' if _vercel_host else '')

# Hôtes autorisés : localhost, domaines Vercel et domaine public de l'app. Plus de '*' :
# un domaine personnalisé doit être déclaré via FRONTEND_URL ou ALLOWED_HOSTS.
raw_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.vercel.app')
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]
if FRONTEND_URL:
    from urllib.parse import urlparse
    _front_host = urlparse(FRONTEND_URL).hostname
    if _front_host and _front_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_front_host)

# ─── Applications installées ─────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',          # Documentation API auto (Swagger/OpenAPI)
]

LOCAL_APPS = [
    'apps.accounts',            # Utilisateurs, authentification
    'apps.services',            # Services (Santé, Admin, PEBCO, ATDA)
    'apps.queues',              # Files d'attente
    'apps.tickets',             # Tickets virtuels
    'apps.notifications',       # Notifications push
    'apps.chatbot',             # Chatbot Rasa
    'apps.stats',               # Statistiques et rapports
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ───────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',    # CORS en premier
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Fichiers statiques (Vercel/Prod)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'montour.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'montour.wsgi.application'

# ─── Base de données (PostgreSQL en prod / Vercel, SQLite en local) ───
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

if DATABASE_URL:
    # connect_timeout court : si la base est injoignable (mauvaise URL,
    # pare-feu...), on échoue vite plutôt que de laisser la fonction
    # serverless bloquée jusqu'au timeout de la plateforme (ce qui se
    # traduit par un crash total plutôt qu'une page d'erreur Django propre).
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        DATABASES['default'].setdefault('OPTIONS', {})['connect_timeout'] = 5
    except ImportError:
        import urllib.parse
        url = urllib.parse.urlparse(DATABASE_URL)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': url.path.lstrip('/'),
                'USER': url.username,
                'PASSWORD': url.password,
                'HOST': url.hostname,
                'PORT': url.port or 5432,
                'OPTIONS': {'connect_timeout': 5},
            }
        }
elif os.getenv('USE_SQLITE', 'True').lower() in ('true', '1', 'yes') and not os.getenv('DB_HOST'):
    # Filet de sécurité : si DATABASE_URL/POSTGRES_URL n'est pas configuré sur
    # Vercel, on écrit au moins dans /tmp plutôt que de crasher sur le
    # filesystem du projet qui est en lecture seule (données non persistées
    # entre invocations, mais l'app reste fonctionnelle en attendant qu'un
    # vrai Postgres soit branché).
    sqlite_db = Path('/tmp/db.sqlite3') if IS_VERCEL else BASE_DIR / 'db.sqlite3'
    if IS_VERCEL:
        warnings.warn("Aucune DATABASE_URL/POSTGRES_URL : SQLite dans /tmp, les comptes et tickets seront PERDUS à chaque redémarrage de la fonction.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_db,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'montour_db'),
            'USER': os.getenv('DB_USER', 'montour_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'montour_pass_2025'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }

# ─── Modèle utilisateur personnalisé ─────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# ─── Validation mots de passe ────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ─────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'   # Fuseau horaire du Bénin
USE_I18N = True
USE_TZ = True

# ─── Fichiers statiques et media ─────────────────────────────
# Pas d'étape de build sur Vercel (pas de buildCommand dans vercel.json) et
# filesystem du projet en lecture seule : on ne peut pas compter sur
# `collectstatic` ayant tourné (le lancer au démarrage de chaque cold start
# était trop lent/risqué — timeouts). WHITENOISE_USE_FINDERS fait servir à
# WhiteNoise les fichiers statiques (admin, DRF browsable API) directement
# depuis les dossiers static/ des apps installées, sans copie ni build.
STATIC_URL = '/static/'
STATIC_ROOT = Path('/tmp/staticfiles') if IS_VERCEL else BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = Path('/tmp/media') if IS_VERCEL else BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Django REST Framework ────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'montour.utils.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/min',
        'user': '120/min',
        'auth': '5/min',
        'register': '5/min',
        'resend': '5/min',
        'recovery': '5/min',
    },
}

# ─── JWT Configuration (SimpleJWT) ───────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ─── CORS (Cross-Origin Resource Sharing) ────────────────────
# L'app web est servie par Django (même origine) : CORS ne concerne que d'autres origines.
# Ouvert à tous en local uniquement ; en production, liste explicite (CORS_ALLOWED_ORIGINS,
# séparées par des virgules) — par défaut seulement le domaine public de l'app.
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS', FRONTEND_URL).split(',') if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]

# ─── Cache ───────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'montour-cache',
    }
}

# ─── Firebase (Cloud Messaging pour notifications push) ───────
FIREBASE_SERVER_KEY = os.getenv('FIREBASE_SERVER_KEY', '')
FIREBASE_SENDER_ID = os.getenv('FIREBASE_SENDER_ID', '')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'montour-benin')

# ─── Email ────────────────────────────────────────────────────
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
# Sans délai, un SMTP injoignable bloquerait la requête jusqu'au timeout de la fonction serverless.
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', 10))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'MonTour <noreply@montour.bj>')
# Sans identifiants SMTP (dev local), les emails sont affichés dans la console
# au lieu d'échouer silencieusement : le lien de vérification y est copiable.
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
    else 'django.core.mail.backends.console.EmailBackend'
)

# Derrière le proxy Vercel, le schéma réel (https) arrive par X-Forwarded-Proto :
# sans cela, les liens générés par build_absolute_uri seraient en http://.
if IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ─── Logging (compatible environnements serverless read-only) ──
LOGS_DIR = BASE_DIR / 'logs'
has_file_logging = False

try:
    if not (IS_VERCEL or os.getenv('AWS_LAMBDA_FUNCTION_NAME')):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        has_file_logging = True
except OSError:
    has_file_logging = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
        'simple': {'format': '{levelname}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'montour.log_handlers.SafeStreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'apps': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR'},
    },
}

if has_file_logging:
    LOGGING['handlers']['file'] = {
        'class': 'logging.FileHandler',
        'filename': LOGS_DIR / 'montour.log',
        'encoding': 'utf-8',
        'formatter': 'verbose',
    }
    LOGGING['loggers']['apps']['handlers'].append('file')

# ─── API Documentation (drf-spectacular) ─────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'MonTour API',
    'DESCRIPTION': 'API de gestion intelligente des files d\'attente — Bénin',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {'email': 'contact@montour.bj'},
    'LICENSE': {'name': 'MIT'},
}

# ─── Paramètres IA MonTour ───────────────────────────────────
MONTOUR_AI = {
    'TFLITE_MODEL_PATH': BASE_DIR / 'ai_models' / 'wait_time_predictor.tflite',
    'RASA_API_URL': os.getenv('RASA_API_URL', 'http://localhost:5005'),
    'PEAK_HOURS': [(8, 10), (11, 13), (15, 17)],
    'PRIORITY_SCORES': {'urgent': 100, 'handicap': 80, 'senior': 60, 'normal': 40},
    'BASE_SERVICE_TIMES': {
        'health': 12, 'admin': 8, 'finance': 10, 'agriculture': 15
    },
}