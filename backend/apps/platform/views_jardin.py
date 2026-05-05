"""
Vistas del modo 'Operar jardín' para el admin del superadmin.

Todas las queries se ejecutan dentro de schema_context(schema) para que
apunten al schema del tenant, mientras la sesión HTTP sigue siendo la del
schema público (superadmin).

URLs registradas en CoremAdminSite.get_urls():
  GET  /admin/jardin/<schema>/                          → jardin_dashboard
  GET  /admin/jardin/<schema>/<modulo>/                 → jardin_modulo
  POST /admin/jardin/<schema>/credenciales/reset/<id>/  → jardin_resetear_password
"""

import secrets
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models as db_models
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_tenants.utils import schema_context

from apps.tenants.models import Domain, Tenant


# ============================================================================
# Metadatos de módulos del jardín
# ============================================================================

MODULOS = [
    {"key": "alumnos",    "title": "Alumnos",    "icon": "👦", "color": "#0d9488", "desc": "Alumnos activos y retirados"},
    {"key": "pagos",      "title": "Pensiones",  "icon": "💳", "color": "#3b82f6", "desc": "Pagos mensuales de pensiones"},
    {"key": "matriculas", "title": "Matrículas", "icon": "📋", "color": "#8b5cf6", "desc": "Matrículas por año escolar"},
    {"key": "caja",       "title": "Caja",       "icon": "💰", "color": "#10b981", "desc": "Ingresos y egresos del jardín"},
    {"key": "aulas",      "title": "Aulas",      "icon": "🏫", "color": "#f59e0b", "desc": "Aulas y ocupación"},
    {"key": "profesores", "title": "Profesores", "icon": "👩‍🏫", "color": "#ec4899", "desc": "Plana docente"},
]

MODULO_MAP = {m["key"]: m for m in MODULOS}

# Colores para badges de estado en las tablas
ESTADO_COLORS = {
    "ACTIVO":       ("#dcfce7", "#166534"),
    "RETIRADO":     ("#fef3c7", "#92400e"),
    "EGRESADO":     ("#f1f5f9", "#475569"),
    "ELIMINADO":    ("#fee2e2", "#991b1b"),
    "PAGADO":       ("#dcfce7", "#166534"),
    "PENDIENTE":    ("#fef3c7", "#92400e"),
    "VENCIDO":      ("#fee2e2", "#991b1b"),
    "EXONERADO":    ("#f1f5f9", "#475569"),
    "INGRESO":      ("#dcfce7", "#166534"),
    "EGRESO":       ("#fee2e2", "#991b1b"),
    "TRIAL":        ("#dbeafe", "#1e40af"),
    "ACTIVA":       ("#dcfce7", "#166534"),
    "MOROSA":       ("#fef3c7", "#92400e"),
    "BLOQUEADA":    ("#fee2e2", "#991b1b"),
    "CANCELADA":    ("#f1f5f9", "#475569"),
}

MESES_ES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _badge(valor):
    """Devuelve un dict con bg/fg para renderizar como badge en el template."""
    bg, fg = ESTADO_COLORS.get(str(valor), ("#f1f5f9", "#374151"))
    return {"valor": valor, "bg": bg, "fg": fg, "is_badge": True}


def _fmt_date(d):
    return d.strftime("%d/%m/%Y") if d else "—"


# ============================================================================
# Recolección de KPIs del jardín
# ============================================================================

def _get_kpis(schema):
    today = date.today()
    mes, anio = today.month, today.year

    with schema_context(schema):
        from apps.students.models import Student
        from apps.payments.models import Payment
        from apps.classrooms.models import Classroom
        from apps.teachers.models import Teacher
        from apps.cashflow.models import CashTransaction

        total_alumnos = Student.objects.filter(estado="ACTIVO").count()
        total_aulas = Classroom.objects.count()
        total_profesores = Teacher.objects.count()

        pagos_mes = Payment.objects.filter(mes=mes, anio=anio)
        pagados_n = pagos_mes.filter(estado="PAGADO").count()
        pendientes_n = pagos_mes.filter(estado="PENDIENTE").count()
        vencidos_n = pagos_mes.filter(estado="VENCIDO").count()

        cobrado_mes = (
            pagos_mes.filter(estado="PAGADO").aggregate(t=db_models.Sum("monto"))["t"]
            or Decimal("0")
        )
        por_cobrar_mes = (
            pagos_mes.filter(estado__in=["PENDIENTE", "VENCIDO"])
            .aggregate(t=db_models.Sum("monto"))["t"]
            or Decimal("0")
        )

        ingresos_mes = (
            CashTransaction.objects.filter(tipo="INGRESO", fecha__year=anio, fecha__month=mes)
            .aggregate(t=db_models.Sum("monto"))["t"]
            or Decimal("0")
        )
        egresos_mes = (
            CashTransaction.objects.filter(tipo="EGRESO", fecha__year=anio, fecha__month=mes)
            .aggregate(t=db_models.Sum("monto"))["t"]
            or Decimal("0")
        )

        morosos = list(
            Payment.objects.filter(
                estado__in=["PENDIENTE", "VENCIDO"],
                fecha_vencimiento__lt=today,
            )
            .select_related("student")
            .order_by("fecha_vencimiento")[:8]
        )

        pagos_recientes = list(
            Payment.objects.filter(estado="PAGADO")
            .select_related("student")
            .order_by("-fecha_pago")[:5]
        )

    return {
        "total_alumnos": total_alumnos,
        "total_aulas": total_aulas,
        "total_profesores": total_profesores,
        "pagados_n": pagados_n,
        "pendientes_n": pendientes_n,
        "vencidos_n": vencidos_n,
        "cobrado_mes": cobrado_mes,
        "por_cobrar_mes": por_cobrar_mes,
        "ingresos_mes": ingresos_mes,
        "egresos_mes": egresos_mes,
        "balance_mes": ingresos_mes - egresos_mes,
        "morosos": morosos,
        "pagos_recientes": pagos_recientes,
        "mes_nombre": MESES_ES[mes],
        "anio_actual": anio,
    }


# ============================================================================
# Vista: Dashboard del jardín
# ============================================================================

def _get_admin_users(schema):
    """Devuelve los usuarios admin del jardín (is_staff=True) y el dominio principal."""
    with schema_context(schema):
        from apps.users.models import User
        admins = list(
            User.objects.filter(is_staff=True)
            .order_by("-is_superuser", "email")
            .values("id", "email", "first_name", "last_name", "last_login", "is_superuser")
        )
    return admins


def jardin_dashboard(request, schema):
    tenant = get_object_or_404(Tenant, schema_name=schema)
    kpis = _get_kpis(schema)
    sub = getattr(tenant, "suscripcion", None)
    admins = _get_admin_users(schema)
    dominio = (
        Domain.objects.filter(tenant=tenant, is_primary=True).first()
        or Domain.objects.filter(tenant=tenant).first()
    )

    context = {
        "tenant": tenant,
        "schema": schema,
        "title": f"Jardín: {tenant.nombre}",
        "modulos": MODULOS,
        "suscripcion": sub,
        "admins": admins,
        "dominio": dominio,
        **kpis,
    }
    return render(request, "admin/jardin/dashboard.html", context)


# ============================================================================
# Recolección de datos por módulo
# ============================================================================

def _get_modulo_data(schema, modulo, page_num, search=""):

    if modulo == "alumnos":
        with schema_context(schema):
            from apps.students.models import Student
            qs = Student.objects.select_related("classroom").order_by("apellidos", "nombres")
            if search:
                qs = qs.filter(
                    db_models.Q(nombres__icontains=search)
                    | db_models.Q(apellidos__icontains=search)
                    | db_models.Q(dni__icontains=search)
                )
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["DNI", "Apellidos y Nombres", "Edad", "Aula", "Estado", "Ingreso"]
            rows = [
                [
                    obj.dni,
                    f"{obj.apellidos}, {obj.nombres}",
                    f"{obj.edad} años",
                    str(obj.classroom) if obj.classroom else "—",
                    _badge(obj.estado),
                    _fmt_date(obj.fecha_ingreso),
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    if modulo == "pagos":
        with schema_context(schema):
            from apps.payments.models import Payment
            qs = Payment.objects.select_related("student").order_by("-anio", "-mes")
            if search:
                qs = qs.filter(
                    db_models.Q(student__nombres__icontains=search)
                    | db_models.Q(student__apellidos__icontains=search)
                    | db_models.Q(student__dni__icontains=search)
                )
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["Alumno", "Periodo", "Monto", "Estado", "Vencimiento", "Pagado", "Método"]
            rows = [
                [
                    str(obj.student),
                    f"{MESES_ES[obj.mes]} {obj.anio}",
                    f"S/ {obj.monto}",
                    _badge(obj.estado),
                    _fmt_date(obj.fecha_vencimiento),
                    _fmt_date(obj.fecha_pago),
                    obj.get_metodo_pago_display() if obj.metodo_pago else "—",
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    if modulo == "matriculas":
        with schema_context(schema):
            from apps.enrollments.models import Enrollment
            qs = Enrollment.objects.select_related("student", "classroom").order_by(
                "-anio_escolar", "student__apellidos"
            )
            if search:
                qs = qs.filter(
                    db_models.Q(student__nombres__icontains=search)
                    | db_models.Q(student__apellidos__icontains=search)
                    | db_models.Q(student__dni__icontains=search)
                )
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["Alumno", "Año", "Aula", "Costo matrícula", "Fecha"]
            rows = [
                [
                    str(obj.student),
                    str(obj.anio_escolar),
                    str(obj.classroom) if obj.classroom else "—",
                    f"S/ {obj.costo_matricula}",
                    _fmt_date(obj.fecha_matricula),
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    if modulo == "caja":
        with schema_context(schema):
            from apps.cashflow.models import CashTransaction
            qs = CashTransaction.objects.select_related("categoria").order_by("-fecha", "-created_at")
            if search:
                qs = qs.filter(descripcion__icontains=search)
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto"]
            rows = [
                [
                    _fmt_date(obj.fecha),
                    _badge(obj.tipo),
                    str(obj.categoria),
                    obj.descripcion,
                    f"S/ {obj.monto}",
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    if modulo == "aulas":
        with schema_context(schema):
            from apps.classrooms.models import Classroom
            qs = Classroom.objects.select_related("profesor_titular").order_by(
                "nivel_edad", "nombre"
            )
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["Nombre", "Nivel", "Alumnos", "Capacidad", "Profesor titular"]
            rows = [
                [
                    obj.nombre,
                    f"{obj.nivel_edad} años",
                    obj.alumnos_count,
                    obj.capacidad,
                    str(obj.profesor_titular) if obj.profesor_titular else "—",
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    if modulo == "profesores":
        with schema_context(schema):
            from apps.teachers.models import Teacher
            qs = Teacher.objects.order_by("apellidos", "nombres")
            if search:
                qs = qs.filter(
                    db_models.Q(nombres__icontains=search)
                    | db_models.Q(apellidos__icontains=search)
                    | db_models.Q(dni__icontains=search)
                )
            total = qs.count()
            paginator = Paginator(qs, 30)
            page = paginator.get_page(page_num)
            columns = ["DNI", "Apellidos y Nombres", "Especialidad", "Teléfono", "Email", "Ingreso"]
            rows = [
                [
                    obj.dni,
                    f"{obj.apellidos}, {obj.nombres}",
                    obj.especialidad or "—",
                    obj.telefono,
                    obj.email or "—",
                    _fmt_date(obj.fecha_ingreso),
                ]
                for obj in page.object_list
            ]
            return columns, rows, page, total

    raise Http404(f"Módulo desconocido: {modulo}")


# ============================================================================
# Vista: Lista de un módulo del jardín
# ============================================================================

def jardin_modulo(request, schema, modulo):
    if modulo not in MODULO_MAP:
        raise Http404

    tenant = get_object_or_404(Tenant, schema_name=schema)
    search = request.GET.get("q", "").strip()
    page_num = request.GET.get("page", 1)

    columns, rows, page, total = _get_modulo_data(schema, modulo, page_num, search)
    meta = MODULO_MAP[modulo]

    context = {
        "tenant": tenant,
        "schema": schema,
        "modulo": modulo,
        "modulo_meta": meta,
        "title": f"{meta['title']} — {tenant.nombre}",
        "columns": columns,
        "rows": rows,
        "page_obj": page,
        "total": total,
        "search": search,
        "modulos": MODULOS,
    }
    return render(request, "admin/jardin/modulo.html", context)


# ============================================================================
# Vista: Resetear contraseña del admin del jardín
# ============================================================================

def jardin_resetear_password(request, schema, user_id):
    """
    Genera una nueva contraseña para un usuario admin del jardín.
    La contraseña se muestra UNA SOLA VEZ en pantalla y se intenta enviar por
    email. Las contraseñas se hashean en BD; nunca son recuperables.

    Solo accesible vía POST desde el panel del jardín (CSRF protegido por el admin).
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    tenant = get_object_or_404(Tenant, schema_name=schema)
    enviar_email = request.POST.get("enviar_email") == "1"

    with schema_context(schema):
        from apps.users.models import User
        user = get_object_or_404(User, id=user_id, is_staff=True)
        new_password = secrets.token_urlsafe(10)
        user.set_password(new_password)
        user.save(update_fields=["password"])

    # Enviar por email (best-effort)
    email_enviado = False
    if enviar_email and user.email:
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f"COREM — Nueva contraseña para {tenant.nombre}",
                message=(
                    f"Hola {user.first_name},\n\n"
                    f"El equipo de COREM ha generado una nueva contraseña "
                    f"para tu acceso a {tenant.nombre}.\n\n"
                    f"Usuario: {user.email}\n"
                    f"Nueva contraseña: {new_password}\n\n"
                    f"Te recomendamos cambiarla al ingresar.\n\n"
                    f"— Equipo COREM"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            email_enviado = True
        except Exception:
            email_enviado = False

    messages.success(request, "Contraseña regenerada correctamente.")

    context = {
        "tenant": tenant,
        "schema": schema,
        "user_email": user.email,
        "user_nombre": f"{user.first_name} {user.last_name}".strip(),
        "new_password": new_password,
        "email_enviado": email_enviado,
        "title": f"Nueva contraseña — {tenant.nombre}",
    }
    return render(request, "admin/jardin/password_reset_done.html", context)
