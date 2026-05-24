"""
Middleware que permite identificar el tenant via header `X-Tenant`
en vez del subdomain del Host.

Caso de uso: el frontend Vercel (servido desde garabato.miniddo.com)
hace requests a api.miniddo.com/api/v1/... Como `api` no es un tenant
real, django-tenants no podría resolver el schema. Este middleware lee
el header `X-Tenant: garabato` que el frontend agrega automáticamente
y activa el schema correcto.

Diseño:
- Si el request trae header `X-Tenant` válido (apunta a un Tenant existente),
  hace switch al schema de ese tenant.
- Si NO trae header o el valor es inválido, deja el comportamiento default
  (django-tenants TenantMainMiddleware lo resuelve por Host).
- DEBE ir DESPUÉS de TenantMainMiddleware en la lista MIDDLEWARE.

Seguridad: `X-Tenant` es solo un identificador (slug), no auth. Las
credenciales JWT/password siguen validándose contra los users del schema
identificado.
"""
import logging

from django.db import connection
from django_tenants.utils import schema_exists, get_tenant_model

logger = logging.getLogger(__name__)


class TenantHeaderMiddleware:
    """Resuelve tenant via header `X-Tenant` (override del subdomain)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._tenant_model = get_tenant_model()

    def __call__(self, request):
        tenant_slug = request.headers.get("X-Tenant", "").strip().lower()

        if tenant_slug and tenant_slug != "public":
            try:
                # Buscar el tenant en el schema public (donde vive la tabla)
                with schema_context_public():
                    tenant = self._tenant_model.objects.filter(
                        schema_name=tenant_slug
                    ).first()

                if tenant:
                    # Activar el schema para todo el request
                    connection.set_tenant(tenant)
                    request.tenant = tenant
                    logger.debug(
                        "TenantHeaderMiddleware: activado schema %s via X-Tenant",
                        tenant_slug,
                    )
                else:
                    logger.warning(
                        "TenantHeaderMiddleware: X-Tenant '%s' no matchea ningún tenant",
                        tenant_slug,
                    )
            except Exception as e:
                logger.exception("TenantHeaderMiddleware error: %s", e)

        return self.get_response(request)


# Helper local para evitar import circular con django_tenants.utils.schema_context
from contextlib import contextmanager


@contextmanager
def schema_context_public():
    """Activa el schema public temporalmente para queries de tenant lookup."""
    previous_tenant = getattr(connection, "tenant", None)
    try:
        from django_tenants.utils import get_public_schema_name
        connection.set_schema_to_public()
        yield
    finally:
        if previous_tenant:
            connection.set_tenant(previous_tenant)
        else:
            connection.set_schema_to_public()
