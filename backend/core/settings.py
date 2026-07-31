"""
Django settings for core project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Security
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-gold-barber-key-change-in-prod')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# Informa ao Django que ele está atrás de um proxy seguro (Nginx com SSL)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'http://140.82.30.186',
    'http://140.82.30.186:8000',
    'http://salaopro.site',
    'https://salaopro.site'
]

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
    'rest_framework_simplejwt.token_blacklist',
    
    # Local apps
    'apps.tenants',
    'apps.accounts',
    'apps.agenda',
    'apps.payments',
]

# Middlewares
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# Database Setup (SQLite in dev mode, customizable via environment variables)
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')

if db_name and db_user and db_password:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static and Media files
STATIC_URL = '/estaticos/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # ou BASE_DIR / 'staticfiles'

MEDIA_URL = '/arquivos/'
MEDIA_ROOT = BASE_DIR / 'media'

# Garante que arquivos enviados (fotos) sejam legíveis por todos os containers (Nginx, etc)
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.Usuario'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/day',
        'login': '5/minute',
        'registro': '10/minute',
        'fila_espera': '100/minute'
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
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
CORS_ALLOW_CREDENTIALS = True

# Email configuration
email_host = os.environ.get('EMAIL_HOST', '').strip()

if email_host:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = email_host
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
    
    # Safe boolean parsing
    tls_val = os.environ.get('EMAIL_USE_TLS', 'True').strip().lower()
    ssl_val = os.environ.get('EMAIL_USE_SSL', 'False').strip().lower()
    
    EMAIL_USE_TLS = tls_val in ('true', '1', 't', 'y', 'yes')
    EMAIL_USE_SSL = ssl_val in ('true', '1', 't', 'y', 'yes')
else:
    # Fallback for local development or when SMTP is not configured
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Salão Pro <notificacoes@salaopro.com.br>')

# WAHA API Configuration
_raw_waha = os.environ.get('WAHA_API_URL', 'http://waha:3000')
if 'localhost' in _raw_waha or '127.0.0.1' in _raw_waha:
    WAHA_API_URL = 'http://waha:3000'
else:
    WAHA_API_URL = _raw_waha

WAHA_SESSION = os.environ.get('WAHA_SESSION', 'default')
WAHA_API_KEY = os.environ.get('WAHA_API_KEY', 'BarbeariaPro!2026')

# Mercado Pago API Configuration
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN', '')

# Configuração de Logging para o Docker
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
