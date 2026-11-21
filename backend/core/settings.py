"""
Django settings for the Git Together backend.

Every environment-specific value comes from backend/.env (see .env.example for
local dev and deploy/env.production.example for the EC2 server).
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes')


def env_list(name, default=''):
    """Comma-separated env var -> list, ignoring blanks."""
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# --- Core ---
# Safe by default: debug is OFF unless .env turns it on (local dev does).
DEBUG = env_bool('DEBUG', False)

SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY or SECRET_KEY.startswith('change-me'):
    if not DEBUG:
        # Never run a public server with a guessable key: it signs login
        # sessions and the email-verification tokens.
        raise ImproperlyConfigured('Set a real SECRET_KEY in backend/.env')
    SECRET_KEY = 'dev-only-insecure-change-me'

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

# Turn on once the site has HTTPS (domain + certificate). Nginx terminates TLS
# and tells Django via the X-Forwarded-Proto header.
if env_bool('USE_HTTPS'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Apps ---
INSTALLED_APPS = [
    'daphne',  # must be first: runserver becomes ASGI (WebSockets in dev)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party
    'rest_framework',
    'rest_framework.authtoken',  # Token table for TokenAuthentication
    'corsheaders',
    'channels',

    # local apps
    'users',
    'profiles',
    'connections',
    'chat',
]

AUTH_USER_MODEL = 'users.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# --- Database (Postgres via docker-compose; see .env.example) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'campus_connect'),
        'USER': os.environ.get('POSTGRES_USER', 'campus_connect'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'campus_connect'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# --- Channels (realtime chat) ---
# The channel layer is how a message saved by one connection reaches every
# browser in that chat: Daphne publishes to Redis, Redis fans it out.
# REDIS_URL wins; REDIS_HOST/REDIS_PORT are the older fallback.
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://{}:{}/0'.format(
    os.environ.get('REDIS_HOST', 'localhost'), os.environ.get('REDIS_PORT', '6379')
)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [REDIS_URL]},
    },
}

# --- DRF ---
REST_FRAMEWORK = {
    # Token first: DRF uses the first class to build the 401 response, and
    # SessionAuthentication has no WWW-Authenticate header, so it would turn
    # "not logged in" into 403. Session auth stays for the browsable API/admin.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Per-user limits for views that opt in with throttle_scope. Counts live
    # in Django's cache (per process), which is fine for one server.
    'DEFAULT_THROTTLE_RATES': {
        'chat_send': '60/min',
        # Per IP address (these users aren't logged in).
        'resend_verification': '5/hour',
    },
}

# --- Email ---
# Console backend prints emails to the terminal / server log (dev and the
# first deploy). To send real mail, set EMAIL_BACKEND to
# django.core.mail.backends.smtp.EmailBackend plus the EMAIL_HOST_* values
# (works with AWS SES SMTP credentials or any SMTP provider).
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'Git Together <no-reply@gittogether.local>'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
# Seconds to wait for the mail server before giving up (default: forever,
# which would hang the signup request).
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 10))

# Where the React app runs. Emailed links (e.g. email verification) point
# here; the frontend page then calls the API.
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

# --- CORS ---
# Only needed in local dev (React on :5173, API on :8000). In production Nginx
# serves both from one address, so the browser never makes cross-origin calls.
CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'
)

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        # Default attributes plus school_email, so passwords like
        # "jdoe2026" are rejected for jdoe@school.edu.
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'first_name', 'last_name', 'email', 'school_email'),
        },
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_TZ = True

# Admin/DRF CSS+JS. `collectstatic` copies them into STATIC_ROOT, and Nginx
# serves that folder at /static/ in production.
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Uploaded files (profile photos). Saved on this server's disk for now;
# Nginx serves MEDIA_ROOT at /media/ in production, Django does in DEBUG.
# Moving to S3 later = install django-storages and set STORAGES["default"].
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
# A relative MEDIA_ROOT is relative to backend/ (absolute paths stay as-is).
MEDIA_ROOT = BASE_DIR / os.environ.get('MEDIA_ROOT', 'media')
# Readable by Nginx (www-data), writable only by the app user.
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Print warnings/errors to the console. On the server that's the Daphne log
# (`journalctl -u gittogether`); with DEBUG off, Django is otherwise silent.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
