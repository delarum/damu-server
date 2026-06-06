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