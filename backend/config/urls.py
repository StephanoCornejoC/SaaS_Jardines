"""URL configuration for tenant schemas."""
from django.contrib import admin
from django.urls import path, include

from apps.platform.views import admin_dashboard
from config.admin_views import enter_tenant_mode_view, exit_tenant_mode_view
from shared.views import protected_media

urlpatterns = [
    # Dashboard del SUPERADMIN (debe ir ANTES de admin.site.urls)
    path("admin/dashboard/", admin_dashboard, name="platform_dashboard"),
    # Modo "Operar jardín": entra/sale (toggle de session var).
    path("admin/op/exit/", exit_tenant_mode_view, name="admin_exit_tenant_mode"),
    path("admin/op/<str:schema>/", enter_tenant_mode_view, name="admin_enter_tenant_mode"),
    # Admin único — su comportamiento cambia según session['active_tenant_schema'].
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/students/", include("apps.students.urls")),
    path("api/v1/teachers/", include("apps.teachers.urls")),
    path("api/v1/classrooms/", include("apps.classrooms.urls")),
    path("api/v1/enrollments/", include("apps.enrollments.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/cashflow/", include("apps.cashflow.urls")),
    path("api/v1/attendance/", include("apps.attendance.urls")),
    path("api/v1/communications/", include("apps.communications.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/migrations/", include("apps.migrations_academic.urls")),
    # SECURITY [VULN-008]: Media files served through authenticated view.
    # Student photos, QR codes, etc. require JWT auth. Never use Django's
    # static() helper for media in any environment.
    path("media/<path:path>", protected_media),
]
