"""Middleware que bloquea el acceso a un tenant con suscripción suspendida."""

import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Cache TTL para el estado de bloqueo del tenant. Sacrificamos hasta 60s de
# latencia en propagar un cambio de estado a cambio de eliminar 1 query DB
# por cada request. La invalidación inmediata se hace con un signal
# post_save/post_delete en TenantSubscription (ver signals.py).
_BLOCKED_CACHE_TTL = 60


def _cache_key(schema_name):
    return f"tenant:blocked:{schema_name}"


def _is_blocked():
    """Devuelve True si el tenant actual está BLOQUEADO. Cacheado 60s."""
    if not getattr(connection, "tenant", None):
        return False
    schema = connection.schema_name
    if schema in ("public", "info"):
        return False

    key = _cache_key(schema)
    cached = cache.get(key)
    if cached is not None:
        return cached

    try:
        from apps.platform.models import TenantSubscription

        is_blocked = TenantSubscription.objects.filter(
            tenant__schema_name=schema,
            estado=TenantSubscription.Estado.BLOQUEADA,
        ).exists()
    except Exception as e:
        # Fail-open: si la DB está caída no convertimos cada request en 402.
        logger.warning(f"BlockSuspendedTenantMiddleware: error consultando estado ({e}); fail-open")
        return False

    cache.set(key, is_blocked, _BLOCKED_CACHE_TTL)
    return is_blocked


def invalidate_blocked_cache(schema_name):
    """Invalidación explícita. La usa el signal post_save de TenantSubscription."""
    cache.delete(_cache_key(schema_name))


# Endpoints permitidos siempre (login/refresh para que el SUPERADMIN
# pueda entrar y desbloquear, y healthcheck).
_BYPASS_PREFIXES = (
    "/admin/",                      # COREM Labs Admin (SuperAdmin Hub)
    "/api/v1/auth/",                # login/refresh
    "/static/",
    "/media/",
    "/health/",                     # Railway healthcheck
)


class BlockSuspendedTenantMiddleware:
    """Si el tenant está BLOQUEADA, devuelve 402 a las APIs del frontend."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if not any(path.startswith(p) for p in _BYPASS_PREFIXES) and _is_blocked():
            return JsonResponse(
                {
                    "code": "subscription_suspended",
                    "detail": (
                        "La suscripción de este jardín está suspendida por falta de pago. "
                        "Por favor contacta al equipo de COREM."
                    ),
                },
                status=402,  # Payment Required
            )
        return self.get_response(request)
