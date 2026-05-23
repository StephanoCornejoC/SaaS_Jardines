"""
Test settings for SAAS_COREM.
Uses PostgreSQL (required by django-tenants) with fast password hashing.
"""

import os

from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

# Allow test hosts: testserver (APIClient default), test.localhost (tenant domain)
ALLOWED_HOSTS = ["*"]

# django-tenants requires PostgreSQL -- SQLite is NOT supported.
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.environ.get("POSTGRES_DB", "test_saas_corem"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        # client_encoding fuerza UTF-8 en la conexión. Sin esto, en máquinas
        # con locale es_PE / es_ES el server Postgres puede mandar mensajes
        # en español (latin-1) en el handshake y psycopg2 rompe con
        # `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3`.
        "OPTIONS": {"client_encoding": "UTF8"},
        "TEST": {"NAME": "test_saas_corem"},
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# --- Performance optimizations for test speed ---
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Use fast (insecure) hasher to speed up user creation in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Disable throttling in tests so API calls are never rate-limited
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

# Disable axes brute-force protection in tests
AXES_ENABLED = False

# Disable audit log in tests for speed
AUDITLOG_INCLUDE_ALL_MODELS = False

# Static files -- use default backend (no manifest hashing)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Media files -- use /tmp for tests
MEDIA_ROOT = "/tmp/saas_corem_test_media"
