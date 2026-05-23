"""Development settings."""
import os
from pathlib import Path

# Carga el .env desde la raíz del backend (sin dependencias extra)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _value = _line.partition("=")
                os.environ.setdefault(_key.strip(), _value.strip())

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.environ.get("DB_NAME", "saas_corem_dev"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5433"),
        # Reutilizar conexiones por 60s (clave para reducir overhead en Railway).
        "CONN_MAX_AGE": 60,
    }
}

# CORS - Allow React dev server
CORS_ALLOW_ALL_ORIGINS = True

# Email - Console backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Cache local en memoria. En dev con un solo worker es suficiente.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Seguridad relajada para dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Deshabilitar django-axes en dev (evita lockouts durante E2E)
AXES_ENABLED = False
