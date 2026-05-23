"""
Middleware de la app config.

`TenantAdminMiddleware`: si `request.session['active_tenant_schema']` está
seteado, activa `schema_context(<schema>)` para esa request. Esto le
permite al admin nativo de Django (que vive en /admin/) operar sobre las
tablas del schema del jardín cuando el SuperAdmin está en "modo Operar".

El switch ON/OFF se hace por las views `enter_tenant_mode_view` y
`exit_tenant_mode_view` (config/admin_views.py).

Ámbito: solo aplica a paths que comienzan con `/admin/`.
"""

from django_tenants.utils import schema_context


class TenantAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if not path.startswith("/admin/"):
            return self.get_response(request)

        session = getattr(request, "session", None)
        schema = session.get("active_tenant_schema") if session else None
        if not schema:
            return self.get_response(request)

        # Validar que el tenant existe; si no, limpiar la sesión y seguir.
        from apps.tenants.models import Tenant

        tenant = Tenant.objects.filter(schema_name=schema).first()
        if tenant is None:
            session.pop("active_tenant_schema", None)
            return self.get_response(request)

        # Inyectar referencias para los templates / each_context.
        request.active_tenant_schema = schema
        request.active_tenant = tenant

        # CRÍTICO: forzar materialización del user en el schema PUBLIC
        # antes del cambio de contexto. Sin esto, el SimpleLazyObject de
        # `request.user` se materializa cuando alguna view lo accede; si
        # eso ocurre dentro del schema_context(<tenant>), Django busca el
        # user en `<tenant>.users_user` (un user distinto que existe en
        # ese schema con id=1, ej. admin@garabato.com en lugar del
        # SuperAdmin de COREM). Tocar `is_authenticated` fuerza la query
        # de auth contra el schema correcto (public).
        _ = request.user.is_authenticated

        with schema_context(schema):
            return self.get_response(request)
