"""
DamuLink Development Settings
Use this locally: manage.py runserver --settings=config.settings.development
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Plain console email in dev — no SendGrid needed
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable S3 locally — use local filesystem
USE_S3 = False
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Relax CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

# Slower token lifetime during dev so you don't keep re-logging in
from datetime import timedelta
SIMPLE_JWT = {
    **SIMPLE_JWT,
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# Print Celery tasks synchronously instead of queuing (no Redis needed to start)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use local memory cache instead of Redis in development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use local memory for sessions too
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Disable Redis-dependent throttling in dev
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
}