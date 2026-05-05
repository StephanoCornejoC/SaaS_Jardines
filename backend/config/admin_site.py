"""
AdminSite custom para COREM.

Filtra qué apps/modelos se muestran según el schema activo (django-tenants):
  - Schema PUBLIC:  modelos de la plataforma SaaS (Tenants, Suscripciones, Cobros, etc.)
  - Schema TENANT:  modelos del jardín (Alumnos, Pagos, Caja, etc.)

El index redirige al dashboard financiero.

Rutas custom añadidas vía get_urls():
  /admin/dashboard/              → Dashboard SaaS con KPIs y gráficos
  /admin/jardin/<schema>/        → Dashboard del jardín con sus módulos
  /admin/jardin/<schema>/<mod>/  → Lista de un módulo del jardín (alumnos, pagos, etc.)
"""

from collections import OrderedDict

from django.contrib import admin
from django.db import connection
from django.urls import reverse


# Apps que SOLO deben verse en el schema público (panel SUPERADMIN)
PUBLIC_ONLY_APPS = {"platform", "tenants"}

# Apps que SOLO deben verse en el schema de un tenant (panel del jardín)
TENANT_ONLY_APPS = {
    "students", "teachers", "classrooms", "enrollments",
    "payments", "cashflow", "attendance", "communications",
    "dashboard", "migrations_academic", "notifications", "reports",
    "auditlog", "axes", "otp_totp", "token_blacklist",
}

# Apps que se muestran en ambos schemas
SHARED_APPS_VISIBLE = {"users", "auth"}


# ============================================================================
# Agrupación visual por secciones
# ============================================================================

PUBLIC_GROUPS = OrderedDict([
    ("Jardines", [
        ("tenants", "Tenant"),
        ("tenants", "Domain"),
    ]),
    ("Suscripciones y cobros", [
        ("platform", "TenantSubscription"),
        ("platform", "PlatformInvoice"),
        ("platform", "PlatformCost"),
        ("platform", "Plan"),
    ]),
    ("Usuarios COREM", [
        ("users", "User"),
        ("auth", "Group"),
    ]),
])

TENANT_GROUPS = OrderedDict([
    ("Gestión escolar", [
        ("students", "Student"),
        ("students", "Guardian"),
        ("students", "MedicalRecord"),
        ("teachers", "Teacher"),
        ("teachers", "TeacherContract"),
        ("classrooms", "Classroom"),
        ("attendance", "Attendance"),
    ]),
    ("Finanzas", [
        ("enrollments", "Enrollment"),
        ("payments", "MonthlyFee"),
        ("payments", "Payment"),
        ("cashflow", "CashCategory"),
        ("cashflow", "CashTransaction"),
        ("cashflow", "MonthlyClosure"),
        ("teachers", "TeacherPayment"),
    ]),
    ("Operaciones", [
        ("communications", "Communication"),
        ("migrations_academic", "AcademicMigration"),
    ]),
    ("Usuarios y permisos", [
        ("users", "User"),
        ("auth", "Group"),
    ]),
])


class CoremAdminSite(admin.AdminSite):
    site_header = "COREM SaaS"
    site_title = "COREM Admin"
    index_title = "Panel de administración"

    # -------------------------------------------------------------------------
    # Helper de schema
    # -------------------------------------------------------------------------

    @property
    def is_public_schema(self):
        return getattr(connection, "schema_name", "public") in ("public", "info")

    # -------------------------------------------------------------------------
    # Home → redirigir al dashboard financiero
    # -------------------------------------------------------------------------

    def index(self, request, extra_context=None):
        from django.shortcuts import redirect
        return redirect(reverse("admin:platform_dashboard"))

    # -------------------------------------------------------------------------
    # Rutas custom: dashboard SaaS + modo jardín
    # -------------------------------------------------------------------------

    def get_urls(self):
        from django.urls import path

        # Imports lazy para evitar importaciones circulares
        from apps.platform.views import admin_dashboard
        from apps.platform.views_jardin import (
            jardin_dashboard,
            jardin_modulo,
            jardin_resetear_password,
        )

        urls = super().get_urls()
        custom = [
            # Dashboard financiero SaaS (home del panel)
            path(
                "dashboard/",
                self.admin_view(admin_dashboard),
                name="platform_dashboard",
            ),
            # Dashboard de un jardín — vista de drill-down
            path(
                "jardin/<str:schema>/",
                self.admin_view(jardin_dashboard),
                name="jardin_dashboard",
            ),
            # Resetear contraseña de un admin del jardín (POST)
            path(
                "jardin/<str:schema>/credenciales/reset/<int:user_id>/",
                self.admin_view(jardin_resetear_password),
                name="jardin_reset_password",
            ),
            # Lista de un módulo del jardín
            path(
                "jardin/<str:schema>/<str:modulo>/",
                self.admin_view(jardin_modulo),
                name="jardin_modulo",
            ),
        ]
        return custom + urls

    # -------------------------------------------------------------------------
    # Filtrado y reagrupación de modelos
    # -------------------------------------------------------------------------

    def get_app_list(self, request, app_label=None):
        original = super().get_app_list(request, app_label)

        # Indexar (app_label, model_name) → entry de Django para preservar permisos
        models_by_key = {}
        for app in original:
            for model in app["models"]:
                key = (app["app_label"], model["object_name"])
                models_by_key[key] = (app, model)

        groups = PUBLIC_GROUPS if self.is_public_schema else TENANT_GROUPS

        result = []
        for group_label, items in groups.items():
            children = []
            for app_label, model_name in items:
                pair = models_by_key.get((app_label, model_name))
                if not pair:
                    continue
                _app, model = pair
                children.append(model)
            if not children:
                continue
            result.append({
                "name": group_label,
                "app_label": group_label.lower().replace(" ", "_"),
                "app_url": "",
                "has_module_perms": True,
                "models": children,
            })
        return result

    def _build_app_dict(self, request, label=None):
        app_dict = super()._build_app_dict(request, label)
        is_public = self.is_public_schema
        filtered = {}
        for app_label, app_data in app_dict.items():
            if is_public:
                if app_label in PUBLIC_ONLY_APPS or app_label in SHARED_APPS_VISIBLE:
                    filtered[app_label] = app_data
            else:
                if app_label in TENANT_ONLY_APPS or app_label in SHARED_APPS_VISIBLE:
                    filtered[app_label] = app_data
        return filtered


corem_admin_site = CoremAdminSite(name="admin")
