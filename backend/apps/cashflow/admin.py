"""Admin de la app cashflow.

Diseño:
  Pulido para que la directora vea de un vistazo el movimiento de caja
  del jardín y rastree cada transacción a su origen (pensión de alumno
  o sueldo de profesor).

  Decisiones:
  - Badges direccionales INGRESO (↑ verde) / EGRESO (↓ rojo).
  - Monto con SIGNO + color: +S/ X verde para ingresos, -S/ X rojo para
    egresos. La directora ve el flujo neto sin sumar mentalmente.
  - Link cruzado al origen: si la transacción vino de un Payment de
    alumno o de un TeacherPayment, se muestra como link clickeable al
    pago original. Cierra el círculo de trazabilidad.
  - MonthlyClosure muestra balance con color y periodo con nombre del mes.
  - Sin list_filter (consistente con el resto del admin).
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import CashCategory, CashTransaction, MonthlyClosure


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _tipo_badge(tipo, display=None):
    """Badge bidireccional para INGRESO/EGRESO con flecha."""
    if tipo == "INGRESO":
        return format_html(
            '<span style="{}"><span style="font-size:9px">▲</span> {}</span>',
            _BADGE.format(bg="#10b981"),
            display or "Ingreso",
        )
    if tipo == "EGRESO":
        return format_html(
            '<span style="{}"><span style="font-size:9px">▼</span> {}</span>',
            _BADGE.format(bg="#ef4444"),
            display or "Egreso",
        )
    return _badge(display or tipo, "#6b7280")


# ---------------------------------------------------------------------------
# CashCategory admin
# ---------------------------------------------------------------------------

@admin.register(CashCategory)
class CashCategoryAdmin(ModelAdmin):
    list_display = (
        "nombre",
        "tipo_badge",
        "sistema_badge",
        "activo_badge",
        "transacciones_count",
    )
    list_display_links = ("nombre",)
    list_filter = ()
    search_fields = ("nombre",)
    readonly_fields = ("created_at",)
    list_per_page = 25
    ordering = ("tipo", "nombre")

    fieldsets = (
        ("Categoría", {"fields": ("nombre", "tipo")}),
        ("Estado", {"fields": ("activo", "es_sistema")}),
        ("Auditoría", {"classes": ("collapse",), "fields": ("created_at",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("transactions")

    @admin.display(description="Tipo", ordering="tipo")
    def tipo_badge(self, obj):
        return _tipo_badge(obj.tipo, obj.get_tipo_display())

    @admin.display(description="Sistema", ordering="es_sistema")
    def sistema_badge(self, obj):
        if obj.es_sistema:
            return _badge("auto", "#8b5cf6")
        return format_html('<span style="color:#94a3b8">—</span>')

    @admin.display(description="Activa", ordering="activo")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color:#10b981">✓</span>')
        return format_html('<span style="color:#ef4444">—</span>')

    @admin.display(description="Transacciones")
    def transacciones_count(self, obj):
        n = len(obj.transactions.all())
        if n == 0:
            return format_html('<span style="color:#94a3b8">—</span>')
        return format_html(
            '<span style="color:#0d9488;font-weight:600">{}</span>', n,
        )


# ---------------------------------------------------------------------------
# CashTransaction admin
# ---------------------------------------------------------------------------

@admin.register(CashTransaction)
class CashTransactionAdmin(ModelAdmin):
    list_display = (
        "fecha",
        "tipo_badge",
        "descripcion",
        "categoria",
        "monto_signed",
        "origen_link",
        "creado_por",
    )
    list_display_links = ("descripcion",)
    list_filter = ()
    search_fields = (
        "descripcion", "categoria__nombre",
        "referencia_pago__student__nombres",
        "referencia_pago__student__apellidos",
        "referencia_teacher_payment__contract__teacher__nombres",
        "referencia_teacher_payment__contract__teacher__apellidos",
    )
    autocomplete_fields = ("referencia_pago", "referencia_teacher_payment")
    readonly_fields = ("created_at", "updated_at", "creado_por")
    ordering = ("-fecha", "-created_at")
    list_per_page = 30
    date_hierarchy = "fecha"

    # JS que esconde/filtra opciones de categoría según el tipo elegido.
    # Espejo de la lógica que ya tiene el frontend de Caja: cuando elegís
    # INGRESO solo aparecen categorías INGRESO; idem EGRESO.
    class Media:
        js = ("admin/js/cashtransaction_filter_categoria.js",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Inyecta data-tipo en las options de categoria para que el JS
        pueda filtrarlas según el tipo seleccionado.

        NOTA: por eso sacamos `categoria` de `autocomplete_fields` —
        el AutocompleteSelect carga options via AJAX, lo que rompe el
        filtro client-side. Con Select normal + data-tipo funciona bien
        para volúmenes razonables (cada jardín tiene 4-10 categorías).
        """
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "categoria":
            # Inyectar data-tipo en cada option al renderizar.
            original_widget = formfield.widget
            original_render = original_widget.create_option

            def create_option_with_tipo(name, value, label, selected,
                                        index, subindex=None, attrs=None):
                option = original_render(
                    name, value, label, selected, index, subindex, attrs,
                )
                actual_pk = getattr(value, "value", value) if value else None
                if actual_pk:
                    try:
                        cat = CashCategory.objects.get(pk=actual_pk)
                        option["attrs"]["data-tipo"] = cat.tipo
                    except CashCategory.DoesNotExist:
                        pass
                return option

            original_widget.create_option = create_option_with_tipo
        return formfield

    fieldsets = (
        ("Transacción", {
            "fields": (("tipo", "categoria"), ("monto", "fecha"), "descripcion"),
        }),
        ("Origen (opcional)", {
            "classes": ("collapse",),
            "fields": ("referencia_pago", "referencia_teacher_payment"),
            "description": (
                "Si la transacción vino de un pago de pensión o sueldo, "
                "queda vinculada acá automáticamente. Edita solo si necesitas "
                "corregir la referencia."
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("creado_por", "created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                "categoria",
                "creado_por",
                "referencia_pago__student",
                "referencia_teacher_payment__contract__teacher",
            )
        )

    @admin.display(description="Tipo", ordering="tipo")
    def tipo_badge(self, obj):
        return _tipo_badge(obj.tipo)

    @admin.display(description="Monto", ordering="monto")
    def monto_signed(self, obj):
        """Monto con signo y color según dirección.

        +S/ X verde para ingresos, -S/ X rojo para egresos. La directora
        ve el flujo neto sin tener que sumar mentalmente columnas
        separadas.
        """
        if obj.tipo == "INGRESO":
            return format_html(
                '<strong style="color:#10b981">+S/ {}</strong>',
                f"{obj.monto:,.2f}",
            )
        if obj.tipo == "EGRESO":
            return format_html(
                '<strong style="color:#ef4444">-S/ {}</strong>',
                f"{obj.monto:,.2f}",
            )
        return format_html('<strong>S/ {}</strong>', f"{obj.monto:,.2f}")

    @admin.display(description="Origen")
    def origen_link(self, obj):
        """Link clickeable al Payment o TeacherPayment que originó esto.

        Cierra el círculo de trazabilidad: desde Caja, vas al pago.
        Desde el pago, podés navegar al alumno o profesor.
        """
        if obj.referencia_pago_id:
            payment = obj.referencia_pago
            url = reverse(
                "admin:payments_payment_change", args=[payment.id],
            )
            mes_nombre = _MESES[payment.mes] if 1 <= payment.mes <= 12 else payment.mes
            return format_html(
                '<a href="{}" style="color:#0d9488;font-weight:600">'
                'Pensión {} · {} {}</a>',
                url, str(payment.student), mes_nombre, payment.anio,
            )
        if obj.referencia_teacher_payment_id:
            tp = obj.referencia_teacher_payment
            url = reverse(
                "admin:teachers_teacherpayment_change", args=[tp.id],
            )
            mes_nombre = _MESES[tp.mes] if 1 <= tp.mes <= 12 else tp.mes
            teacher = tp.contract.teacher
            return format_html(
                '<a href="{}" style="color:#6366f1;font-weight:600">'
                'Sueldo {} · {} {}</a>',
                url, str(teacher), mes_nombre, tp.anio,
            )
        return format_html(
            '<span style="color:#94a3b8;font-style:italic">manual</span>'
        )


# ---------------------------------------------------------------------------
# MonthlyClosure admin
# ---------------------------------------------------------------------------

@admin.register(MonthlyClosure)
class MonthlyClosureAdmin(ModelAdmin):
    list_display = (
        "periodo_display",
        "ingresos_display",
        "egresos_display",
        "balance_display",
        "cerrado_por",
        "fecha_cierre",
    )
    list_display_links = ("periodo_display",)
    list_filter = ()
    search_fields = ("anio", "observaciones")
    readonly_fields = (
        "mes",
        "anio",
        "total_ingresos",
        "total_egresos",
        "balance",
        "cerrado_por",
        "fecha_cierre",
    )
    ordering = ("-anio", "-mes")
    list_per_page = 30

    fieldsets = (
        ("Periodo", {"fields": (("mes", "anio"),)}),
        ("Totales", {"fields": (("total_ingresos", "total_egresos"), "balance")}),
        ("Cierre", {"fields": ("cerrado_por", "fecha_cierre", "observaciones")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("cerrado_por")

    @admin.display(description="Periodo", ordering="-anio")
    def periodo_display(self, obj):
        mes_nombre = _MESES[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        return format_html(
            '<strong>{}</strong> <span style="color:#94a3b8">{}</span>',
            mes_nombre, obj.anio,
        )

    @admin.display(description="Ingresos", ordering="total_ingresos")
    def ingresos_display(self, obj):
        return format_html(
            '<span style="color:#10b981;font-weight:600">+S/ {}</span>',
            f"{obj.total_ingresos:,.2f}",
        )

    @admin.display(description="Egresos", ordering="total_egresos")
    def egresos_display(self, obj):
        return format_html(
            '<span style="color:#ef4444;font-weight:600">-S/ {}</span>',
            f"{obj.total_egresos:,.2f}",
        )

    @admin.display(description="Balance", ordering="balance")
    def balance_display(self, obj):
        """Balance del mes con color según signo. Verde si positivo,
        rojo si negativo, gris si exactamente cero."""
        if obj.balance > 0:
            color = "#10b981"
            sign = "+"
        elif obj.balance < 0:
            color = "#ef4444"
            sign = ""  # el signo ya viene en el valor negativo
        else:
            color = "#6b7280"
            sign = ""
        return format_html(
            '<strong style="color:{};font-size:13px">{}S/ {}</strong>',
            color, sign, f"{obj.balance:,.2f}",
        )

    def has_add_permission(self, request):
        # Los cierres mensuales se generan via management command
        # (`cerrar_mes`) o action del API. NO se crean a mano desde admin.
        return False

    def has_change_permission(self, request, obj=None):
        # Tampoco se editan: son snapshots históricos del balance.
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo el superadmin del Hub puede borrarlos en caso de cierre
        # erróneo (raro). Permitimos delete con confirmación nativa.
        return super().has_delete_permission(request, obj)
