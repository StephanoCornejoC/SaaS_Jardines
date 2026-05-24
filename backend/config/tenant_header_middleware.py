"""
Middleware que permite identificar el tenant cuando frontend y backend
viven en hosts diferentes (Vercel + Railway, distintos subdomains).

Problema:
- Frontend en `garabato.miniddo.com` (Vercel) hace requests a `api.miniddo.com` (Railway).
- TenantMainMiddleware de django-tenants resuelve el schema según `request.get_host()`.
- Como `api.miniddo.com` no es un tenant, cae al schema `public` y selecciona
  `PUBLIC_SCHEMA_URLCONF` (urls_public.py) que NO tiene `/api/v1/...`. → 404.

Solución:
- Este middleware corre ANTES de TenantMainMiddleware.
- Lee el subdomain del header `Origin` del browser (estándar CORS) o del
  header explícito `X-Tenant` como fallback.
- Si encuentra un tenant válido, modifica `request.META["HTTP_HOST"]` para
  que TenantMainMiddleware lo resuelva como ese tenant.
- Después, todo funciona como si el request viniera del subdomain del tenant.

Detección del tenant slug (en orden):
1. Header `Origin` (ej. "https://garabato.miniddo.com" → "garabato")
2. Header `X-Tenant` (ej. "garabato")

Si no hay match, el comportamiento queda default (TenantMainMiddleware
resuelve por Host real).
"""
import logging
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)


def _extract_tenant_from_origin(origin_value):
    """
    Extrae el slug del tenant del header Origin.
    Ej: "https://garabato.miniddo.com" → "garabato"
        "https://miniddo.com"           → None (apex, no tenant)
        "http://localhost:3000"         → None
    """
    if not origin_value:
        return None
    try:
        parsed = urlparse(origin_value)
        host = parsed.hostname or ""
        base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "miniddo.com")
        # Solo aceptamos subdomains del dominio base configurado
        if host.endswith(f".{base_domain}") and host != base_domain:
            return host[: -len(f".{base_domain}")]
    except Exception:
        pass
    return None


class TenantHeaderMiddleware:
    """
    Resuelve tenant del Origin / X-Tenant header cuando frontend y backend
    están en hosts diferentes (multi-host SaaS). DEBE ir ANTES de
    TenantMainMiddleware en MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_slug = None

        # 1. Intentar extraer del Origin (estándar CORS, lo envía el browser)
        origin = request.headers.get("Origin", "")
        tenant_slug = _extract_tenant_from_origin(origin)

        # 2. Fallback al header explícito X-Tenant
        if not tenant_slug:
            x_tenant = request.headers.get("X-Tenant", "").strip().lower()
            if x_tenant and x_tenant != "public":
                tenant_slug = x_tenant

        if tenant_slug:
            base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "miniddo.com")
            new_host = f"{tenant_slug}.{base_domain}"
            # Modificar HTTP_HOST para que TenantMainMiddleware lo vea como
            # el subdomain del tenant. Esto fuerza la resolución correcta del
            # schema Y del URLCONF (urls.py vs urls_public.py).
            request.META["HTTP_HOST"] = new_host
            logger.debug(
                "TenantHeaderMiddleware: redirected HTTP_HOST to %s (from Origin/X-Tenant)",
                new_host,
            )

        return self.get_response(request)
