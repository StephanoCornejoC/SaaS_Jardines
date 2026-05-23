"""Production settings for Railway deployment."""
import os

from .base import *  # noqa: F401,F403

# Fail fast if SECRET_KEY is not explicitly set in production
if not os.environ.get("DJANGO_SECRET_KEY"):
    raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

DEBUG = False
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.environ.get("PGDATABASE"),
        "USER": os.environ.get("PGUSER"),
        "PASSWORD": os.environ.get("PGPASSWORD"),
        "HOST": os.environ.get("PGHOST"),
        "PORT": os.environ.get("PGPORT", "5432"),
        # Reutilizar conexiones por 60s. Reduce ~30% del overhead de
        # handshake TCP por request en Railway.
        "CONN_MAX_AGE": 60,
    }
}

# CORS - Only allow Vercel frontend
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CORS_ALLOW_CREDENTIALS = True

# Cache compartido entre workers de gunicorn vía Postgres.
# Antes usábamos Redis, pero al consolidar los crons en `daily_saas_run`
# Redis dejó de tener uso. DatabaseCache nos da un store compartido sin
# pagar un servicio adicional.
# Requisito de deploy: `python manage.py createcachetable` (idempotente).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "corem_cache",
        "TIMEOUT": 300,
        "OPTIONS": {"MAX_ENTRIES": 5000},
    }
}

# Security hardening
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
# Eximir /health/ del redirect HTTP->HTTPS. El healthcheck de Railway pingea
# por la red interna (100.64.x.x) sin pasar por el proxy que setea
# X-Forwarded-Proto, asi que Django lo ve como HTTP y redirige con 301.
# Railway espera 2xx, no 3xx, por eso el healthcheck falla. Exentando este
# path puntual el resto sigue forzando HTTPS.
SECURE_REDIRECT_EXEMPT = [r"^health/?$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

# Email - SMTP (Brevo por defecto en prod, configurable via env)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp-relay.brevo.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# Timeout corto del SMTP: si Brevo no responde en 10s, fallar rapido en
# vez de colgar el request 5+ minutos (TCP timeout default). Critico para
# el flow de "crear jardin" que hace send_mail al final.
EMAIL_TIMEOUT = 10

# Si las credenciales SMTP NO estan seteadas, switch a console backend
# (imprime el email al log en vez de intentar enviarlo). Util durante el
# deploy inicial cuando Brevo todavia no esta configurado (D6 todavia
# pendiente). Sin esto, send_mail() se cuelga esperando TCP handshake al
# servidor SMTP con credenciales vacias y mata al gunicorn worker.
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ------- Sentry (D8) -------
# Solo inicializa si SENTRY_DSN está seteado. Mientras no exista la cuenta
# Sentry, el sistema funciona sin error reporting (lo cual es OK para arrancar).
SENTRY_DSN = os.environ.get("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        integrations=[DjangoIntegration()],
        # 10% sampling para performance monitoring (free tier tope: 10K txns/mes)
        traces_sample_rate=0.1,
        # NO mandar PII (cumplimos privacy con apoderados/menores)
        send_default_pii=False,
        # Tag de release con SHA de commit (Railway lo expone como env var)
        release=os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown"),
    )
