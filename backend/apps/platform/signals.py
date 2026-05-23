"""Signals para invalidar caches cuando cambia una TenantSubscription."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .middleware import invalidate_blocked_cache
from .models import TenantSubscription


@receiver(post_save, sender=TenantSubscription)
@receiver(post_delete, sender=TenantSubscription)
def _invalidate_blocked_cache_on_change(sender, instance, **kwargs):
    """
    Invalida la caché de estado bloqueado del tenant cada vez que la
    suscripción cambia (alta, edición, borrado). Garantiza que un cambio
    de estado del SuperAdmin se refleje inmediatamente en el middleware
    sin esperar al TTL de 60s.
    """
    schema = getattr(getattr(instance, "tenant", None), "schema_name", None)
    if schema:
        invalidate_blocked_cache(schema)
