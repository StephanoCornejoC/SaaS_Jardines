"""URL configuration for the public schema (panel del SUPERADMIN)."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "saas-corem"})


urlpatterns = [
    # Admin del superadmin — rutas del jardín se registran en CoremAdminSite.get_urls()
    path("admin/", admin.site.urls),
    path("health/", health_check),
]
