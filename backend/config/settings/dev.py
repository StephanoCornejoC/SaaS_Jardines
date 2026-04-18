"""Development settings."""
import os

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.environ.get("POSTGRES_DB", "saas_corem"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
    }
}

# CORS - Allow React dev server
CORS_ALLOW_ALL_ORIGINS = True

# Email - Console backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Cache - use local memory when Redis is not available (for E2E testing without Redis)
if os.environ.get("USE_LOCMEM_CACHE", "True").lower() == "true":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
        }
    }

# Celery - eager mode when Redis unavailable (tasks execute synchronously)
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "True").lower() == "true"

# Security relaxed for dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Disable django-axes brute-force protection in dev (avoids lockouts during E2E)
AXES_ENABLED = False
