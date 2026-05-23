"""URL configuration for the public schema (panel del SUPERADMIN)."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView

from apps.platform.views import admin_dashboard
from apps.platform.views_cron import daily_cron_manual_view, daily_cron_token_view
from config.admin_views import enter_tenant_mode_view, exit_tenant_mode_view


def health_check(request):
    return JsonResponse({"status": "ok", "service": "saas-corem"})


urlpatterns = [
    # Apex redirect: por ahora `miniddo.com/` apunta al backend Railway, asi
    # que `/` lo mandamos al admin. Cuando D9 (Vercel frontend) este listo,
    # el apex `miniddo.com` va a apuntar a Vercel y ese frontend serviria
    # la landing publica. Este redirect deja de ser relevante porque las
    # requests de `/` ya no llegan a Railway.
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    # Cron diario (D7): endpoint con token para GitHub Actions + boton manual
    # del admin Kiddo. AMBOS deben ir ANTES de admin.site.urls porque comparten
    # el prefijo /admin/.
    path("api/v1/cron/daily/", daily_cron_token_view, name="cron_daily_token"),
    path("admin/cron/daily/", daily_cron_manual_view, name="cron_daily_manual"),
    path("admin/dashboard/", admin_dashboard, name="platform_dashboard"),
    path("admin/op/exit/", exit_tenant_mode_view, name="admin_exit_tenant_mode"),
    path("admin/op/<str:schema>/", enter_tenant_mode_view, name="admin_enter_tenant_mode"),
    path("admin/", admin.site.urls),
    path("health/", health_check),
]
