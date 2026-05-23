"""
Views auxiliares del COREM Labs Admin para entrar y salir del modo
Operar Jardín. Estas dos URLs solo manipulan la sesión y redirigen al
admin. El switch real (activar schema_context) lo hace
`TenantAdminMiddleware`.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect

from apps.tenants.models import Tenant


@staff_member_required
def enter_tenant_mode_view(request, schema):
    """Setea `active_tenant_schema` en la sesión y redirige al index del
    admin (que en modo tenant muestra los modelos del jardín)."""
    tenant = get_object_or_404(Tenant, schema_name=schema)
    request.session["active_tenant_schema"] = tenant.schema_name
    request.session["active_tenant_nombre"] = tenant.nombre
    return redirect("/admin/")


@staff_member_required
def exit_tenant_mode_view(request):
    """Borra `active_tenant_schema` de la sesión y vuelve al Hub."""
    request.session.pop("active_tenant_schema", None)
    request.session.pop("active_tenant_nombre", None)
    return redirect("/admin/")
