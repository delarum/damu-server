"""
DamuLink Base Settings
Shared across all environments.
"""
from pathlib import Path
from decouple import config as env
from datetime import timedelta
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

DEBUG = False

ALLOWED_HOSTS = []

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "storages",
    "django_celery_beat",
    "drf_yasg",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.donors",
    "apps.hospitals",
    "apps.matching",
    "apps.gamification",
    "apps.ussd",
    "apps.payments",
    "apps.notifications",
    "apps.verification",
    "apps.audit",
    "apps.third_party",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL'),
        conn_max_age=600
    )
}
# ---------------------------------------------------------------------------
# Cache & Sessions (Redis)
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "donor_search": "60/hour",
        "contact_initiation": "20/hour",
        "login": "10/hour",
    },
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "EXCEPTION_HANDLER": "utils.exceptions.custom_exception_handler",
}

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ---------------------------------------------------------------------------
# File Storage (S3 / R2)
# ---------------------------------------------------------------------------
USE_S3 = os.environ.get("USE_S3", "False") == "True"

if USE_S3:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "damulink-secure-docs")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "af-south-1")
    AWS_DEFAULT_ACL = "private"          # CRITICAL: never public
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {"ServerSideEncryption": "AES256"}
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")  # For Cloudflare R2

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
DEFAULT_FROM_EMAIL = "noreply@damulink.co.ke"

# ---------------------------------------------------------------------------
# Third-party API Keys
# ---------------------------------------------------------------------------
# Africa's Talking
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "")
AT_SENDER_ID = os.environ.get("AT_SENDER_ID", "DamuLink")
AT_USSD_CODE = os.environ.get("AT_USSD_CODE", "*384*123#")

# Smile Identity
SMILE_PARTNER_ID = os.environ.get("SMILE_PARTNER_ID", "")
SMILE_API_KEY = os.environ.get("SMILE_API_KEY", "")

# M-Pesa Daraja
MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "")
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "")
MPESA_STK_URL = os.environ.get(
    "MPESA_STK_URL",
    "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
)
MPESA_TOKEN_URL = os.environ.get(
    "MPESA_TOKEN_URL",
    "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
)
MPESA_CALLBACK_URL = os.environ.get(
    "MPESA_CALLBACK_URL", "https://damulink.co.ke/api/v1/payments/mpesa/callback/"
)

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Google Maps
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# ---------------------------------------------------------------------------
# Encryption key for sensitive fields (Fernet)
# ---------------------------------------------------------------------------
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Security headers (enforced in production settings)
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

FERNET_KEYS = [env('FIELD_ENCRYPTION_KEY')]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]