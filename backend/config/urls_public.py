"""URL configuration for the public schema (no tenant)."""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok", "service": "saas-corem"})


urlpatterns = [
    path("corem-panel-x9k2/", admin.site.urls),
    path("health/", health_check),
]
