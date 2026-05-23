"""
Base settings for SAAS_COREM project.
Common settings shared between dev and prod.
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def _get_secret_key():
    key = os.environ.get("DJANGO_SECRET_KEY")
    if key:
        return key
    # Only allow insecure key in development
    import warnings
    warnings.warn("Using insecure SECRET_KEY. Set DJANGO_SECRET_KEY in environment.", stacklevel=2)
    return "django-insecure-dev-only-DO-NOT-USE-IN-PRODUCTION"

SECRET_KEY = _get_secret_key()

# --- Multi-Tenancy (django-tenants) ---
SHARED_APPS = [
    "django_tenants",
    "apps.tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Admin nativo con CoremAdminSite (filtra modelos por schema y los reagrupa)
    "config.apps.CoremAdminConfig",
    # Third party (shared)
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "auditlog",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
    # Users must be shared for public schema auth
    "apps.users",
    # Plataforma SaaS (modelos en schema público: planes, suscripciones, cobros, gastos)
    "apps.platform",
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.users",
    "apps.students",
    "apps.teachers",
    "apps.classrooms",
    "apps.enrollments",
    "apps.payments",
    "apps.cashflow",
    "apps.migrations_academic",
    "apps.notifications",
    "apps.reports",
    "apps.dashboard",
    "apps.attendance",
    "apps.communications",
    # Shared apps that also need per-tenant tables
    "rest_framework_simplejwt.token_blacklist",
    "auditlog",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# --- Middleware ---
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "axes.middleware.AxesMiddleware",
    "apps.platform.middleware.BlockSuspendedTenantMiddleware",
    # Detecta /admin/jardin/<schema>/... y activa schema_context para que
    # el TenantOpAdminSite opere en el schema correcto.
    "config.middleware.TenantAdminMiddleware",
]

ROOT_URLCONF = "config.urls"
PUBLIC_SCHEMA_URLCONF = "config.urls_public"

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

# --- Database ---
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# --- Auth ---
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- JWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # Single-session enforcement: solo un login activo por usuario
        "apps.users.single_session.JWTSingleSessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "100/minute",
    },
}

# --- Axes (brute force protection) ---
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_CALLABLE = None
AXES_RESET_ON_SUCCESS = True

# --- Audit Log ---
# Solo modelos sensibles. Auditar todos genera muchas escrituras y agranda
# la tabla de logs (cada UPDATE = 1 registro).
AUDITLOG_INCLUDE_ALL_MODELS = False
AUDITLOG_INCLUDE_TRACKING_MODELS = (
    "students.Student",
    "students.Guardian",
    "enrollments.Enrollment",
    "payments.Payment",
    "payments.MonthlyFee",
    "cashflow.CashTransaction",
    "cashflow.MonthlyClosure",
    # No incluir users.User aquí: causa joins con tablas tenant al
    # operar en schema público (auditlog explora relaciones inversas).
)

# --- Cache ---
# Default seguro para cualquier entorno (locmem). Sobreescrito en dev.py
# (locmem) y prod.py (DatabaseCache compartido entre workers).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "corem-default",
        "TIMEOUT": 300,
    }
}

# --- i18n ---
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# --- Static & Media ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Sin esto, Django no encuentra `backend/static/admin/css/corem.css` y
# devuelve 404, rompiendo el branding del admin del SuperAdmin.
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# SECURITY [VULN-008]: Media files (student photos, QR codes) contain
# sensitive data. They are served via shared.views.protected_media which
# requires JWT authentication. Do NOT use Django's static() helper for
# media serving in any environment (dev or prod).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Email ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@miniddo.com")

# Email del SuperAdmin de la plataforma SaaS. Lo usa `notificar_vencimientos`
# y demás jobs del cron consolidado para reportar trials por vencer y cobros
# del día. Override por env var en producción.
SUPERADMIN_EMAIL = os.environ.get("SUPERADMIN_EMAIL", "stephano.cornejoc@gmail.com")

# Dominio base del SaaS Kiddo. Se usa en `apps/tenants/admin.py` para armar
# el dominio default de cada jardín nuevo (`<schema>.miniddo.com`) cuando
# Stephano hace "+ Crear nuevo jardín" desde el Hub.
#
# El wildcard SSL universal de Cloudflare ya cubre `*.miniddo.com`, así que
# cada subdominio generado tiene HTTPS automático sin más configuración.
#
# Override por env var en producción si llegáramos a tener un dominio
# alternativo (white-label, segundo SaaS, etc.).
TENANT_BASE_DOMAIN = os.environ.get("TENANT_BASE_DOMAIN", "miniddo.com")


# Datos para el cobro mensual del SaaS al jardín (PlatformInvoice).
# Estos valores aparecen en el email de cobro y en el QR Yape adjunto.
COREM_BUSINESS_NAME = os.environ.get("COREM_BUSINESS_NAME", "COREM Labs S.A.C.")
COREM_YAPE_PHONE = os.environ.get("COREM_YAPE_PHONE", "")  # Ej: "999888777"
COREM_PLIN_PHONE = os.environ.get("COREM_PLIN_PHONE", "")  # Ej: "999888777"

# Branding del admin se configura en `config/admin_site.py` (CoremAdminSite)
# y en `templates/admin/base_site.html`. Las legacy settings de jazzmin
# fueron removidas — la integración con jazzmin/django-unfold se descartó
# por incompatibilidad con Python 3.14.
