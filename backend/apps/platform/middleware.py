"""Middleware que bloquea el acceso a un tenant con suscripción suspendida."""

from django.db import connection
from django.http import JsonResponse


def _is_blocked():
    """Devuelve True si el tenant actual está BLOQUEADO."""
    if not getattr(connection, "tenant", None):
        return False
    schema = connection.schema_name
    if schema in ("public", "info"):
        return False
    # Import diferido para evitar problemas de carga
    from apps.platform.models import TenantSubscription

    return TenantSubscription.objects.filter(
        tenant__schema_name=schema,
        estado=TenantSubscription.Estado.BLOQUEADA,
    ).exists()


# Endpoints permitidos siempre (admin del superadmin, login/refresh, estáticos).
_BYPASS_PREFIXES = (
    "/admin/",          # admin Django — superadmin y jardín
    "/api/v1/auth/",    # login / refresh JWT
    "/static/",
    "/media/",
    "/health/",
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
