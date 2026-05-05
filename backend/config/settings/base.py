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

# --- Cache (memoria local en dev, configurar Redis en prod) ---
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
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@corem.pe")

# --- Branding admin nativo (sustituye los settings de jazzmin) ---
# Usamos admin.site.site_title/site_header en config/urls.py, ver tienda.
# Aquí dejamos JAZZMIN_SETTINGS solo como referencia inactiva.
_JAZZMIN_SETTINGS_LEGACY = {
    "site_title": "COREM Admin",
    "site_header": "COREM SaaS",
    "site_brand": "COREM",
    "site_logo": None,
    "site_logo_classes": "img-circle",
    "welcome_sign": "Panel de administración del jardín",
    "copyright": "COREM Labs S.A.C.",
    "search_model": ["students.Student", "teachers.Teacher", "users.User"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "show_ui_builder": False,
    "icons": {
        # Plataforma SaaS
        "platform.Plan":               "fas fa-tag",
        "platform.TenantSubscription": "fas fa-handshake",
        "platform.PlatformInvoice":    "fas fa-file-invoice-dollar",
        "platform.PlatformCost":       "fas fa-receipt",
        # Tenants y usuarios
        "tenants.Tenant": "fas fa-school",
        "tenants.Domain": "fas fa-globe",
        "users.User": "fas fa-user-shield",
        # Gestión escolar
        "students.Student": "fas fa-child",
        "students.Guardian": "fas fa-user-friends",
        "students.MedicalRecord": "fas fa-notes-medical",
        "teachers.Teacher": "fas fa-chalkboard-teacher",
        "teachers.TeacherContract": "fas fa-file-contract",
        "teachers.TeacherPayment": "fas fa-money-check-alt",
        "classrooms.Classroom": "fas fa-door-open",
        "attendance.Attendance": "fas fa-calendar-check",
        # Finanzas
        "enrollments.Enrollment": "fas fa-clipboard-list",
        "payments.MonthlyFee": "fas fa-file-invoice-dollar",
        "payments.Payment": "fas fa-credit-card",
        "cashflow.CashCategory": "fas fa-tags",
        "cashflow.CashTransaction": "fas fa-exchange-alt",
        "cashflow.MonthlyClosure": "fas fa-lock",
        # Operaciones
        "communications.Communication": "fas fa-envelope",
        "notifications.EmailLog": "fas fa-paper-plane",
        "dashboard.DashboardMetric": "fas fa-chart-line",
        "migrations_academic.AcademicMigration": "fas fa-graduation-cap",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "order_with_respect_to": [
        "platform",
        "tenants",
        "users",
        "students",
        "teachers",
        "classrooms",
        "attendance",
        "enrollments",
        "payments",
        "cashflow",
        "communications",
        "notifications",
        "dashboard",
        "migrations_academic",
    ],
    "custom_links": {},
    "topmenu_links": [
        {"name": "Dashboard COREM", "url": "/admin/dashboard/", "permissions": ["auth.view_user"]},
        {"name": "Crear jardín",    "url": "admin:tenants_tenant_crear_jardin", "permissions": ["auth.view_user"]},
        {"name": "Volver al SaaS",  "url": "/", "new_window": True},
    ],
    "usermenu_links": [
        {"name": "Volver al SaaS", "url": "/", "new_window": True},
    ],
    "language_chooser": False,
    "changeform_format": "horizontal_tabs",
}

_JAZZMIN_UI_TWEAKS_LEGACY = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-teal",
    "accent": "accent-teal",
    "navbar": "navbar-teal navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
    "actions_sticky_top": True,
}
