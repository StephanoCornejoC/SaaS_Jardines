"""URL routes para la API pública de la app platform."""
from django.urls import path

from .views import tier_status

urlpatterns = [
    path("tier-status/", tier_status, name="platform_tier_status"),
]
