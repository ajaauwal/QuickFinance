import os
import sys
from pathlib import Path
import environ
from django.contrib.messages import constants as messages

# Initialize environment variables
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure the 'apps' directory is added to Python path
APPS_DIR = BASE_DIR / 'apps'
if APPS_DIR.exists():
    sys.path.append(str(APPS_DIR))

# Load environment variables from .env
env = environ.Env()
env_file = BASE_DIR / '.env'
if env_file.exists():
    env.read_env(str(env_file))
else:
    raise FileNotFoundError(f".env file not found at {env_file}")

# Security settings
SECRET_KEY = env('SECRET_KEY', default='your-django-secret-key')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# Website URL
WEBSITE_URL = env('WEBSITE_URL', default='http://127.0.0.1:8000/')

# Installed applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Custom apps
    'apps.accounts',
    'apps.transactions',
    'apps.notifications',
    'apps.services',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'django_extensions',
    'corsheaders',
    'africastalking',
    'channels',
    'social_django',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Enable debug toolbar only in DEBUG mode
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
}

# Middleware settings
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Enable debug toolbar middleware only in DEBUG mode
if DEBUG:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'quickfinance.urls'
WSGI_APPLICATION = 'quickfinance.wsgi.application'
ASGI_APPLICATION = 'quickfinance.asgi.application'

# Database configuration (SQLite)
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

AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'

# Collects all static files in this directory when running collectstatic
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Ensure Django knows where to find static files during development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',  # If using Google login
    'django.contrib.auth.backends.ModelBackend',
]

# Email configuration
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/home/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Django messages
MESSAGE_TAGS = {messages.ERROR: 'danger'}

# Templates
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

# Security settings
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)

# API Keys
VTPASS_BASE_URL = env('VTPASS_API_BASE_URL', default='https://sandbox.vtpass.com/api')
VTPASS_PUBLIC_KEY = env('VTPASS_PUBLIC_KEY', default='')
VTPASS_SECRET_KEY = env('VTPASS_SECRET_KEY', default='')

AMADEUS_API_KEY = env('AMADEUS_API_KEY', default='')
AMADEUS_API_SECRET = env('AMADEUS_API_SECRET', default='')
AMADEUS_BASE_URL = env('AMADEUS_BASE_URL', default='https://test.api.amadeus.com/v1')

PAYSTACK_PUBLIC_KEY = env('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_BASE_URL = env('PAYSTACK_BASE_URL', default='https://api.paystack.co/')
PAYSTACK_PAYMENT_URL = env('PAYSTACK_PAYMENT_URL', default='https://api.paystack.co/transaction/initialize')
PAYSTACK_TRANSFER_URL = env('PAYSTACK_TRANSFER_URL', default='https://api.paystack.co/transfer')
PAYSTACK_CALLBACK_URL = env('PAYSTACK_CALLBACK_URL', default='')

TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')

# OTP configuration
OTP_EXPIRY_SECONDS = env.int('OTP_EXPIRY_SECONDS', default=30)

# Internal IPs (for Debug Toolbar)
INTERNAL_IPS = ['127.0.0.1']

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', default='')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
}
