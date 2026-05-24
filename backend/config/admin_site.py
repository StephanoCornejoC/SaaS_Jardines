"""
AdminSite custom: Miniddo · Admin.

Diseño:
  Un único `CoremAdminSite` (alias `admin.site`, namespace `admin:`).
  El "modo Operar Jardín" se activa por SESIÓN (no por URL distinta):
  cuando `request.session['active_tenant_schema']` está seteado, el
  middleware `TenantAdminMiddleware` activa `schema_context(<schema>)`
  para esa request, y `_build_app_dict / get_app_list` muestran los
  modelos del jardín en vez de los del SaaS.

  URLs auxiliares:
    /admin/op/<schema>/   → setea la sesión y redirige a /admin/
    /admin/op/exit/       → borra la sesión y redirige a /admin/

  Esto evita los conflictos de namespace que ocurren al usar dos
  AdminSite con `app_name='admin'`: cuando current_app='tenantadmin' y
  los templates de Django hacen `{% url 'admin:index' %}`, Django mapea
  el namespace al instance_name (current_app) que requiere kwargs y
  rompe con NoReverseMatch.

  Nota histórica: este admin se llamaba "Hub" cuando era multi-vertical
  (jardines + empresas web). El vertical de empresas se eliminó y el
  admin quedó dedicado al SaaS Miniddo. El nombre de la clase
  `CoremAdminSite` se mantiene por compatibilidad con migrations y
  URLconf — el branding visible es "Miniddo · Admin".
"""

from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import admin
from django.db import connection
from django.db.models import Sum


# Apps del schema público (admin del SuperAdmin de Miniddo)
PUBLIC_ONLY_APPS = {"platform", "tenants"}

# Apps de schema tenant (modelos del jardín)
TENANT_ONLY_APPS = {
    "students", "teachers", "classrooms", "enrollments",
    "payments", "cashflow", "attendance", "communications",
    "dashboard", "migrations_academic", "notifications", "reports",
    "auditlog", "axes", "otp_totp", "token_blacklist",
}

# Apps que se muestran en ambos modos
SHARED_APPS_VISIBLE = {"users", "auth"}


# ============================================================================
# Pilares del admin Miniddo (modo NORMAL — sin tenant activo)
# ============================================================================

PUBLIC_GROUPS = OrderedDict([
    ("Jardines (clientes)", [
        ("tenants", "Tenant"),
        ("tenants", "Domain"),
    ]),
    ("Suscripciones y cobros", [
        ("platform", "TenantSubscription"),
        ("platform", "PlatformInvoice"),
        ("platform", "Plan"),
    ]),
    ("Costos del SaaS", [
        ("platform", "PlatformCost"),
    ]),
    ("Sistema", [
        ("users", "User"),
        ("auth", "Group"),
    ]),
])

# ============================================================================
# Grupos del modo Operar Jardín — modelos del tenant agrupados
# ============================================================================

TENANT_GROUPS = OrderedDict([
    ("Gestión escolar", [
        ("students", "Student"),
        ("students", "Guardian"),
        ("students", "MedicalRecord"),
        ("teachers", "Teacher"),
        ("teachers", "TeacherContract"),
        ("classrooms", "Classroom"),
        ("attendance", "Attendance"),
    ]),
    ("Finanzas", [
        ("enrollments", "Enrollment"),
        ("payments", "MonthlyFee"),
        ("payments", "Payment"),
        ("cashflow", "CashCategory"),
        ("cashflow", "CashTransaction"),
        ("cashflow", "MonthlyClosure"),
        ("teachers", "TeacherPayment"),
    ]),
    ("Operaciones", [
        ("communications", "Communication"),
        ("migrations_academic", "AcademicMigration"),
        ("notifications", "EmailLog"),
    ]),
    ("Sistema del jardín", [
        ("users", "User"),
    ]),
])


def _active_tenant_schema(request):
    """Schema del jardín activo en la sesión, o None si estamos en modo SaaS."""
    if request is None:
        return None
    session = getattr(request, "session", None)
    if session is None:
        return None
    return session.get("active_tenant_schema")


class CoremAdminSite(admin.AdminSite):
    """AdminSite del SaaS Miniddo. Cambia la lista de modelos visibles
    según `request.session['active_tenant_schema']`:
      - vacío → admin de Miniddo (modelos shared agrupados en pilares)
      - seteado → Operar Jardín (modelos del jardín activo)
    """

    site_header = "Miniddo · Admin"
    site_title = "Miniddo"
    index_title = "Panel central"
    enable_nav_sidebar = True
    index_template = "admin/corem_index.html"

    # ----- Helpers de modo -----

    def is_tenant_mode(self, request):
        return bool(_active_tenant_schema(request))

    # ----- Filter de modelos según modo -----

    def _build_app_dict(self, request, label=None):
        app_dict = super()._build_app_dict(request, label)

        if self.is_tenant_mode(request):
            # En modo Operar Jardín: solo modelos del jardín
            return {
                k: v for k, v in app_dict.items()
                if k in TENANT_ONLY_APPS or k in SHARED_APPS_VISIBLE
            }

        # Modo SaaS: solo modelos del schema público
        return {
            k: v for k, v in app_dict.items()
            if k in PUBLIC_ONLY_APPS or k in SHARED_APPS_VISIBLE
        }

    def get_app_list(self, request, app_label=None):
        original = super().get_app_list(request, app_label)

        models_by_key = {}
        for app in original:
            for model in app["models"]:
                models_by_key[(app["app_label"], model["object_name"])] = (app, model)

        in_tenant = self.is_tenant_mode(request)
        groups = TENANT_GROUPS if in_tenant else PUBLIC_GROUPS

        result = []
        for group_label, items in groups.items():
            children = []
            for app_label_, model_name in items:
                pair = models_by_key.get((app_label_, model_name))
                if pair is None:
                    continue
                _app, model = pair
                children.append(model)

            # Lazy load: si es el grupo "Jardines (clientes)" en modo SaaS,
            # agregamos un acceso directo por jardín al final. NO cargamos
            # los sub-modelos — cada jardín es un solo link que entra al
            # modo Operar. Eso mantiene el sidebar liviano con N jardines
            # (1 query barata + N líneas de HTML).
            if not in_tenant and group_label.startswith("Jardines"):
                children.extend(_jardin_items(active_schema=None))

            if children:
                result.append({
                    "name": group_label,
                    "app_label": group_label.lower().replace(" ", "_").replace("·", ""),
                    "app_url": "",
                    "has_module_perms": True,
                    "models": children,
                })

        # En modo Operar, agregar grupo "Otros jardines" al final para
        # poder cambiar rápido sin volver al panel principal.
        if in_tenant:
            current_schema = _active_tenant_schema(request)
            others = _jardin_items(active_schema=current_schema)
            if others:
                result.append({
                    "name": "Otros jardines",
                    "app_label": "otros_jardines",
                    "app_url": "",
                    "has_module_perms": True,
                    "models": others,
                })

        return result

    # ----- Index (admin Miniddo muestra grilla de jardines + KPIs) -----

    def index(self, request, extra_context=None):
        ctx = {"in_tenant_mode": self.is_tenant_mode(request)}

        if not ctx["in_tenant_mode"]:
            ctx.update(_build_admin_index_context())

        if extra_context:
            ctx.update(extra_context)
        return super().index(request, extra_context=ctx)

    # ----- each_context: pasar info del tenant activo a templates -----

    def each_context(self, request):
        ctx = super().each_context(request)
        ctx["active_tenant_schema"] = getattr(request, "active_tenant_schema", None)
        ctx["active_tenant"] = getattr(request, "active_tenant", None)
        return ctx


# ============================================================================
# Lazy-load helpers para el sidebar
# ============================================================================

def _jardin_items(active_schema=None):
    """Lista los jardines como items del sidebar del admin.

    Cada item apunta a `/admin/op/<schema>/`, que activa el modo Operar
    de ese jardín (vía sesión + middleware). El item NO incluye sub-
    modelos: estos se renderizan recién al entrar al jardín. Esto mantiene
    el sidebar liviano cuando crece a 100+ tenants.

    Args:
        active_schema: si está seteado, EXCLUYE ese tenant de la lista.
                       Útil para mostrar "Otros jardines" en modo Operar.

    Returns:
        Lista de dicts compatibles con la estructura de items del admin.
    """
    from apps.tenants.models import Tenant

    qs = Tenant.objects.exclude(schema_name__in=("public", "info"))
    if active_schema:
        qs = qs.exclude(schema_name=active_schema)
    qs = qs.only("id", "schema_name", "nombre").order_by("nombre")

    items = []
    for t in qs:
        items.append({
            "name": t.nombre,
            "object_name": f"TenantOp_{t.schema_name}",
            "admin_url": f"/admin/op/{t.schema_name}/",
            # No mostramos "+ Añadir" en estos items: agregar tenants se
            # hace desde el changelist de Tenant ("Crear nuevo jardín").
            "add_url": None,
            "view_only": False,
            "perms": {
                "add": False, "change": True, "delete": False, "view": True,
            },
        })
    return items


# ============================================================================
# Helpers de contexto para el admin Miniddo
# ============================================================================

# Orden de prioridad de jardines en el grid: lo accionable arriba.
_TENANT_PRIORITY = {
    "BLOQUEADA": 0,
    "MOROSA": 1,
    "TRIAL": 2,
    "ACTIVA": 3,
    None: 4,           # sin suscripción
    "CANCELADA": 5,
}


def _build_admin_index_context():
    """Construye el contexto del index del admin Miniddo: KPIs, alertas, jardines.

    Una sola pasada por la BD (sin N+1):
      - 1 query para TenantSubscription (select_related tenant)
      - 1 query para Tenant
      - 1 query para PlatformCost (agg suma mes)
      - 1 query para PlatformInvoice PENDIENTE (filtro por vencimiento próximo)
    """
    from apps.platform.models import PlatformCost, PlatformInvoice, TenantSubscription
    from apps.tenants.models import Tenant

    today = date.today()
    week_ahead = today + timedelta(days=7)

    # --- Jardines (cards) ---
    subs = list(TenantSubscription.objects.select_related("tenant"))
    subs_by_tenant = {s.tenant_id: s for s in subs}

    tenants_data = []
    for t in Tenant.objects.exclude(schema_name__in=("public", "info")):
        sub = subs_by_tenant.get(t.id)
        estado = sub.estado if sub else None
        tenants_data.append({
            "id": t.id,
            "nombre": t.nombre,
            "schema_name": t.schema_name,
            "ruc": t.ruc,
            "estado": estado,
            "get_estado_display": sub.get_estado_display() if sub else None,
            "search_needle": f"{t.nombre} {t.schema_name} {t.ruc}".lower(),
            "_sort": (_TENANT_PRIORITY.get(estado, 99), t.nombre.lower()),
        })
    tenants_data.sort(key=lambda x: x["_sort"])

    # --- KPIs ---
    total_jardines = len(tenants_data)
    jardines_activos = sum(1 for t in tenants_data if t["estado"] == "ACTIVA")
    morosos_count = sum(1 for t in tenants_data if t["estado"] in ("MOROSA", "BLOQUEADA"))
    mrr_mes = sum(
        (s.precio_acordado for s in subs if s.estado == TenantSubscription.Estado.ACTIVA),
        Decimal("0"),
    )
    costos_mes = (
        PlatformCost.objects
        .filter(fecha__year=today.year, fecha__month=today.month)
        .aggregate(total=Sum("monto"))
        ["total"]
        or Decimal("0")
    )

    # --- Alertas ---
    alertas = []
    bloqueados = [t for t in tenants_data if t["estado"] == "BLOQUEADA"]
    if bloqueados:
        alertas.append({
            "tono": "critico",
            "icono": "■",
            "texto": f"{len(bloqueados)} jardín{'es' if len(bloqueados) > 1 else ''} bloqueado{'s' if len(bloqueados) > 1 else ''} por impago",
        })
    if morosos_count - len(bloqueados) > 0:
        n = morosos_count - len(bloqueados)
        alertas.append({
            "tono": "warning",
            "icono": "▲",
            "texto": f"{n} jardín{'es' if n > 1 else ''} en mora",
        })

    trials_vencen = [
        s for s in subs
        if s.estado == TenantSubscription.Estado.TRIAL
        and s.trial_hasta and s.trial_hasta <= week_ahead
    ]
    if trials_vencen:
        alertas.append({
            "tono": "info",
            "icono": "◷",
            "texto": f"{len(trials_vencen)} trial{'es' if len(trials_vencen) > 1 else ''} vence{'n' if len(trials_vencen) > 1 else ''} en los próximos 7 días",
        })

    invoices_proximas = (
        PlatformInvoice.objects
        .filter(
            estado=PlatformInvoice.Estado.PENDIENTE,
            fecha_vencimiento__lte=week_ahead,
            fecha_vencimiento__gte=today,
        )
        .count()
    )
    if invoices_proximas:
        alertas.append({
            "tono": "info",
            "icono": "$",
            "texto": f"{invoices_proximas} cobro{'s' if invoices_proximas > 1 else ''} vence{'n' if invoices_proximas > 1 else ''} esta semana",
        })

    return {
        "tenants": tenants_data,
        "kpi_jardines_activos": jardines_activos,
        "kpi_jardines_total": total_jardines,
        "kpi_morosos": morosos_count,
        "kpi_mrr_mes": mrr_mes,
        "kpi_costos_mes": costos_mes,
        "alertas": alertas,
    }


corem_admin_site = CoremAdminSite(name="admin")
