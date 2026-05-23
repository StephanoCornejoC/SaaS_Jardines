from django.apps import AppConfig


class PlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.platform"
    verbose_name = "Plataforma SaaS"

    def ready(self):
        # Conecta los signals que invalidan caches al cambiar TenantSubscription
        from . import signals  # noqa: F401
