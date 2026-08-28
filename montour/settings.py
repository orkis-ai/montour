# =============================================================
# MonTour — settings.py
# Configuration principale Django
# =============================================================

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Sécurité ────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-montour-change-in-prod-2025')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Autoriser localhost, IPs locales et domaines Vercel
raw_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.vercel.app,*')
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]

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

# ─── Base de données (SQLite par défaut si env USE_SQLITE est True ou si Postgres non configuré) ───────
if os.getenv('USE_SQLITE', 'True').lower() in ('true', '1', 'yes'):
    # Sur Vercel (serverless lambda), seul /tmp est accessible en écriture
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        sqlite_db = Path('/tmp') / 'db.sqlite3'
    else:
        sqlite_db = BASE_DIR / 'db.sqlite3'

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
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
CORS_ALLOW_ALL_ORIGINS = True
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
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'MonTour <noreply@montour.bj>'

# ─── Logging (compatible environnements serverless read-only) ──
LOGS_DIR = BASE_DIR / 'logs'
has_file_logging = False

try:
    if not (os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME')):
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
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
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