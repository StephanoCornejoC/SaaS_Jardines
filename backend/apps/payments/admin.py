"""Admin de la app payments.

Diseño:
  Pulido para que la directora vea el estado financiero de cada alumno
  de un vistazo: cuánto debe, cuándo vence, cuántos días de atraso.

  Decisiones:
  - Badge dinámico de estado que muestra VENCIDO si fecha_vencimiento ya
    pasó y el pago no fue confirmado (el modelo guarda PENDIENTE pero la
    realidad operativa es vencido — la directora necesita ese highlight).
  - Periodo con nombre del mes ("Marzo 2026") en lugar de "3/2026".
  - Monto formateado S/ con separador de miles.
  - Indicador de días de atraso (rojo si >7, ámbar si 1-7).
  - 3 acciones bulk: marcar pagado (con fecha hoy), marcar exonerado,
    forzar VENCIDO (raramente útil, pero existe).
  - Link clickeable al alumno.
"""

from datetime import date

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import MonthlyFee, Payment


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


# ---------------------------------------------------------------------------
# MonthlyFee admin
# ---------------------------------------------------------------------------

@admin.register(MonthlyFee)
class MonthlyFeeAdmin(ModelAdmin):
    """Configuración de la pensión mensual de cada alumno por año.

    La directora rara vez edita esto desde el admin (el frontend ya tiene
    UI). Lo mantenemos pulido por si hace falta auditar.
    """
    list_display = (
        "student_link",
        "anio_badge",
        "monto_display",
        "dia_vencimiento_display",
        "pagos_anio",
    )
    list_display_links = ("student_link",)
    list_filter = ()
    search_fields = ("student__nombres", "student__apellidos", "student__dni")
    autocomplete_fields = ("student",)
    readonly_fields = ("created_at",)
    ordering = ("-anio_escolar", "student__apellidos")
    list_per_page = 30

    fieldsets = (
        ("Pensión mensual", {
            "fields": (("student", "anio_escolar"), "monto_mensual", "dia_vencimiento"),
        }),
        ("Auditoría", {"classes": ("collapse",), "fields": ("created_at",)}),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("student")
            .prefetch_related("payments")
        )

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Año", ordering="-anio_escolar")
    def anio_badge(self, obj):
        anio_actual = date.today().year
        color = "#10b981" if obj.anio_escolar == anio_actual else "#94a3b8"
        return _badge(str(obj.anio_escolar), color)

    @admin.display(description="Monto mensual", ordering="monto_mensual")
    def monto_display(self, obj):
        return format_html('<strong>S/ {}</strong>', f"{obj.monto_mensual:,.2f}")

    @admin.display(description="Vencimiento", ordering="dia_vencimiento")
    def dia_vencimiento_display(self, obj):
        return format_html(
            '<span style="color:#475569">día <strong>{}</strong> de cada mes</span>',
            obj.dia_vencimiento,
        )

    @admin.display(description="Pagos del año")
    def pagos_anio(self, obj):
        total = len(obj.payments.all())
        pagados = sum(
            1 for p in obj.payments.all() if p.estado == Payment.Estado.PAGADO
        )
        if total == 0:
            return format_html('<span style="color:#94a3b8">—</span>')
        return format_html(
            '<span style="color:#0d9488;font-weight:600">{} pagados</span>'
            '<span style="color:#94a3b8"> / {}</span>',
            pagados, total,
        )


# ---------------------------------------------------------------------------
# Payment admin
# ---------------------------------------------------------------------------

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        "student_link",
        "periodo_display",
        "monto_display",
        "estado_badge",
        "vencimiento_display",
        "atraso_display",
        "metodo_display",
    )
    list_display_links = ("student_link",)
    list_filter = ()
    search_fields = (
        "student__nombres", "student__apellidos", "student__dni",
        "comprobante",
    )
    autocomplete_fields = ("student", "monthly_fee")
    readonly_fields = ("created_at", "updated_at", "registrado_por")
    ordering = ("-anio", "-mes", "student__apellidos")
    list_per_page = 30
    date_hierarchy = "fecha_vencimiento"
    actions = (
        "accion_marcar_pagado_hoy",
        "accion_marcar_exonerado",
        "accion_marcar_vencido",
    )

    fieldsets = (
        ("Alumno", {"fields": (("student", "monthly_fee"),)}),
        ("Periodo", {"fields": (("mes", "anio"), ("monto", "fecha_vencimiento"))}),
        ("Estado de pago", {
            "fields": ("estado", ("fecha_pago", "metodo_pago"), "comprobante"),
        }),
        ("Observaciones", {"fields": ("observaciones",)}),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("registrado_por", "created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("student", "monthly_fee", "registrado_por")
        )

    # ---- columnas ----

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Periodo", ordering="-anio")
    def periodo_display(self, obj):
        mes_nombre = _MESES[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        return format_html(
            '<strong>{}</strong> <span style="color:#94a3b8">{}</span>',
            mes_nombre, obj.anio,
        )

    @admin.display(description="Monto", ordering="monto")
    def monto_display(self, obj):
        return format_html('<strong>S/ {}</strong>', f"{obj.monto:,.2f}")

    @admin.display(description="Estado", ordering="estado")
    def estado_badge(self, obj):
        """Badge que combina el estado guardado con la realidad operativa.

        Si está PENDIENTE pero la fecha de vencimiento ya pasó, mostramos
        "VENCIDO" en rojo para que la directora actúe. El estado en BD
        no cambia automáticamente — el cron `daily_saas_run` lo maneja
        a nivel global. Esto es solo visual.
        """
        colors = {
            "PAGADO":    "#10b981",
            "PENDIENTE": "#f59e0b",
            "VENCIDO":   "#ef4444",
            "EXONERADO": "#3b82f6",
        }
        # Detección de "vencido virtual": PENDIENTE + ya pasó la fecha.
        if (
            obj.estado == Payment.Estado.PENDIENTE
            and obj.fecha_vencimiento
            and obj.fecha_vencimiento < date.today()
        ):
            return _badge("vencido", colors["VENCIDO"])
        return _badge(obj.get_estado_display(), colors.get(obj.estado, "#6b7280"))

    @admin.display(description="Vencimiento", ordering="fecha_vencimiento")
    def vencimiento_display(self, obj):
        if not obj.fecha_vencimiento:
            return "—"
        return obj.fecha_vencimiento.strftime("%d/%m/%Y")

    @admin.display(description="Atraso")
    def atraso_display(self, obj):
        if obj.estado in (Payment.Estado.PAGADO, Payment.Estado.EXONERADO):
            return format_html('<span style="color:#94a3b8">—</span>')
        if not obj.fecha_vencimiento:
            return "—"
        diff = (date.today() - obj.fecha_vencimiento).days
        if diff <= 0:
            return format_html('<span style="color:#94a3b8">al día</span>')
        color = "#ef4444" if diff > 7 else "#f59e0b"
        return format_html(
            '<span style="color:{};font-weight:600">{} día{}</span>',
            color, diff, "s" if diff != 1 else "",
        )

    @admin.display(description="Método", ordering="metodo_pago")
    def metodo_display(self, obj):
        if not obj.metodo_pago:
            return format_html('<span style="color:#94a3b8">—</span>')
        colors = {
            "EFECTIVO":      "#10b981",
            "YAPE":          "#8b5cf6",
            "PLIN":          "#06b6d4",
            "TRANSFERENCIA": "#3b82f6",
            "OTRO":          "#6b7280",
        }
        return _badge(
            obj.get_metodo_pago_display(),
            colors.get(obj.metodo_pago, "#6b7280"),
        )

    # ---- acciones bulk ----

    @admin.action(description="Marcar como PAGADO (fecha hoy)")
    def accion_marcar_pagado_hoy(self, request, queryset):
        today = date.today()
        n = queryset.update(estado=Payment.Estado.PAGADO, fecha_pago=today)
        self.message_user(
            request,
            f"{n} pago(s) marcado(s) como PAGADO con fecha {today.strftime('%d/%m/%Y')}. "
            "Nota: estas marcas masivas NO crean CashTransactions automáticas — "
            "se usan para limpiar registros viejos. El flujo normal de pago "
            "desde el frontend sí genera el ingreso en Caja.",
            messages.SUCCESS,
        )

    @admin.action(description="Marcar como EXONERADO")
    def accion_marcar_exonerado(self, request, queryset):
        n = queryset.update(estado=Payment.Estado.EXONERADO)
        self.message_user(
            request, f"{n} pago(s) marcado(s) como EXONERADO.",
            messages.SUCCESS,
        )

    @admin.action(description="Forzar estado VENCIDO")
    def accion_marcar_vencido(self, request, queryset):
        n = queryset.update(estado=Payment.Estado.VENCIDO)
        self.message_user(
            request, f"{n} pago(s) marcado(s) como VENCIDO.",
            messages.WARNING,
        )
