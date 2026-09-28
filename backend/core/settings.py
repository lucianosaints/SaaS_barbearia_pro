"""
Django settings for core project.
"""

from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('true', '1', 'yes')


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)

# Security
DEBUG = env_bool('DJANGO_DEBUG')
AGENDA_NOTIFICATIONS_ASYNC = env_bool('AGENDA_NOTIFICATIONS_ASYNC', not DEBUG)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if DEBUG and not SECRET_KEY:
    SECRET_KEY = 'django-insecure-local-development-only-not-for-production'
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '')
if not DEBUG:
    if len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-'):
        raise ImproperlyConfigured('Configure DJANGO_SECRET_KEY com pelo menos 50 caracteres aleatórios.')
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('Configure DJANGO_ALLOWED_HOSTS com os domínios da aplicação.')

# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'rest_framework_simplejwt.token_blacklist',
    
    # Local apps
    'apps.tenants',
    'apps.accounts',
    'apps.agenda',
    'apps.payments',
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.subscription_middleware.SubscriptionMiddleware',
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

# SQLite fica restrito ao desenvolvimento; produção exige o PostgreSQL informado.
DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite' if DEBUG else '').strip().lower()
if DB_ENGINE not in ('sqlite', 'postgresql'):
    raise ImproperlyConfigured('Configure DB_ENGINE=postgresql em produção.')
if not DEBUG and DB_ENGINE != 'postgresql':
    raise ImproperlyConfigured('SQLite não é permitido em produção neste projeto.')
if DB_ENGINE == 'postgresql':
    if not DEBUG:
        missing = [name for name in ('DB_NAME', 'DB_USER', 'DB_HOST') if not os.environ.get(name, '').strip()]
        if missing:
            raise ImproperlyConfigured('Configure as variáveis do PostgreSQL: ' + ', '.join(missing))
    database_options = {
        'sslmode': os.environ.get('DB_SSLMODE', 'prefer'),
        'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '10')),
    }
    if os.environ.get('DB_SSLROOTCERT'):
        database_options['sslrootcert'] = os.environ['DB_SSLROOTCERT']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'sass_barber_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': database_options,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('DB_SQLITE_PATH', BASE_DIR / 'db.sqlite3'),
            'OPTIONS': {'timeout': 20, 'transaction_mode': 'IMMEDIATE'},
            'TEST': {'NAME': os.environ.get('TEST_DATABASE_NAME')},
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.accounts.validators.StrongPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
ADMIN_URL = 'admin/' if DEBUG else 'painel-master/'
STATIC_URL = '/static/' if DEBUG else '/estaticos/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/arquivos/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_DIRECTORY', str(BASE_DIR / 'media')))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.Usuario'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.RevocableJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'auth_ip': os.environ.get('AUTH_IP_RATE_LIMIT', '20/min'),
        'auth_account': os.environ.get('AUTH_ACCOUNT_RATE_LIMIT', '5/min'),
        'site_visit': os.environ.get('SITE_VISIT_RATE_LIMIT', '30/min'),
        'anon': '100/minute', 'user': '1000/day', 'fila_espera': '100/minute',
    },
}

# O cache de produção é compartilhado pelos workers do Gunicorn. Redis/Memcached
# pode ser configurado no deploy substituindo este backend.
CACHES = {
    'default': {
        'BACKEND': (
            'django.core.cache.backends.locmem.LocMemCache'
            if DEBUG else 'django.core.cache.backends.redis.RedisCache'
        ),
        'LOCATION': (
            'barbeiro-pro-local-cache'
            if DEBUG else os.environ.get('CACHE_URL', 'redis://redis:6379/1')
        ),
        'TIMEOUT': 300,
        'KEY_PREFIX': 'barbeiro-pro',
    }
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173' if DEBUG else '')
CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '0' if DEBUG else '3600'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env_bool('DJANGO_HSTS_PRELOAD')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
# Ative apenas quando o proxy remove o header fornecido pelo cliente e o define corretamente.
if env_bool('DJANGO_TRUST_PROXY'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Email configuration for local development
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend' if os.environ.get('EMAIL_HOST') else 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'notificacoes@goldenbarber.com.br')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', False)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', not EMAIL_USE_SSL)
EMAIL_TIMEOUT = 10
EMAIL_ALERT_TO = env_list('EMAIL_ALERT_TO')
PUBLIC_FRONTEND_URL = os.environ.get('PUBLIC_FRONTEND_URL', 'http://localhost:3000' if DEBUG else '').rstrip('/')
PASSWORD_RESET_TIMEOUT = int(os.environ.get('PASSWORD_RESET_TIMEOUT', '1800'))
if EMAIL_USE_SSL and EMAIL_USE_TLS:
    raise ImproperlyConfigured('EMAIL_USE_SSL e EMAIL_USE_TLS nao podem estar ativos ao mesmo tempo.')
if not DEBUG and EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    missing = [name for name in ('EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL') if not os.environ.get(name, '').strip()]
    if missing:
        raise ImproperlyConfigured('Configure as variaveis SMTP: ' + ', '.join(missing))
if not DEBUG and not PUBLIC_FRONTEND_URL.startswith('https://'):
    raise ImproperlyConfigured('Configure PUBLIC_FRONTEND_URL com uma origem HTTPS valida.')

FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
WAHA_API_URL = os.environ.get("WAHA_API_URL", "http://waha:3000")
WAHA_SESSION = os.environ.get("WAHA_SESSION", "default")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
