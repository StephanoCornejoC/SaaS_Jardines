"""URL configuration for tenant schemas."""
from django.contrib import admin
from django.urls import include, path

from shared.views import protected_media

# Branding del admin nativo
admin.site.site_title = "COREM Admin"
admin.site.site_header = "COREM SaaS — Panel"
admin.site.index_title = "Panel de administración"

urlpatterns = [
    # Admin (accesible en schema tenant solo si alguien llega por ese dominio;
    # el superadmin lo usa desde localhost que ya apunta al schema public)
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
