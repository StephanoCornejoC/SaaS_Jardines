"""URL configuration for the public schema (panel del SUPERADMIN)."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.platform.views import admin_dashboard
from config.admin_views import enter_tenant_mode_view, exit_tenant_mode_view


def health_check(request):
    return JsonResponse({"status": "ok", "service": "saas-corem"})


urlpatterns = [
    path("admin/dashboard/", admin_dashboard, name="platform_dashboard"),
    path("admin/op/exit/", exit_tenant_mode_view, name="admin_exit_tenant_mode"),
    path("admin/op/<str:schema>/", enter_tenant_mode_view, name="admin_enter_tenant_mode"),
    path("admin/", admin.site.urls),
    path("health/", health_check),
]
