"""Admin de la app teachers.

Diseño:
  Pulido para que Stephano (SuperAdmin) y la directora puedan gestionar
  profesores, contratos y pagos desde el admin Django sin pasar por el
  frontend.

  Decisiones:
  - Avatares con inicial coloreada por tipo (titular teal / auxiliar índigo).
  - Badges de color para tipo de profesor, tipo de contrato, estado activo
    del contrato, método de pago.
  - Links: wa.me al teléfono del profesor, mailto al email, link al teacher
    desde contratos y pagos.
  - Contadores en list_display: contratos activos, aulas a cargo.
  - Acción bulk en contratos: marcar finalizado (setea fecha_fin=hoy y activo=False).
  - Sin list_filter (consistente con la decisión de students — el search y
    los badges cubren los casos reales).
"""

from datetime import date

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, TabularInline
from django.urls import reverse
from django.utils.html import format_html

from .models import Teacher, TeacherContract, TeacherPayment


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------

_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


def _wa_link(telefono):
    if not telefono:
        return "—"
    digits = "".join(c for c in telefono if c.isdigit())
    if not digits:
        return telefono
    intl = digits if digits.startswith("51") else f"51{digits}"
    return format_html(
        '<a href="https://wa.me/{}" target="_blank" rel="noopener" '
        'style="color:#25d366;font-weight:600">{} ↗</a>',
        intl, telefono,
    )


def _mail_link(email):
    if not email:
        return "—"
    return format_html(
        '<a href="mailto:{}" style="color:#0d9488">{}</a>', email, email,
    )


_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class ContractInline(TabularInline):
    """Contratos del profesor — visible en el form del Teacher."""
    model = TeacherContract
    extra = 0
    fields = ("tipo", "sueldo", "fecha_inicio", "fecha_fin", "activo")
    show_change_link = True
    verbose_name = "Contrato"
    verbose_name_plural = "Contratos del profesor"


class PaymentInline(TabularInline):
    """Pagos del contrato — visible en el form del TeacherContract."""
    model = TeacherPayment
    extra = 0
    fields = ("mes", "anio", "monto", "fecha_pago", "metodo_pago", "comprobante")
    ordering = ("-anio", "-mes")
    verbose_name = "Pago"
    verbose_name_plural = "Pagos del contrato"


# ---------------------------------------------------------------------------
# Teacher admin
# ---------------------------------------------------------------------------

@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    list_display = (
        "avatar_mini",
        "dni",
        "nombre_completo",
        "tipo_badge",
        "especialidad",
        "contratos_activos",
        "aulas_a_cargo",
        "telefono_link",
        "email_link",
        "fecha_ingreso",
    )
    list_display_links = ("dni", "nombre_completo")
    list_filter = ()
    search_fields = (
        "dni", "nombres", "apellidos", "email", "especialidad",
        "user__email",
    )
    ordering = ("apellidos", "nombres")
    list_per_page = 30
    date_hierarchy = "fecha_ingreso"
    readonly_fields = ("created_at", "updated_at")
    inlines = [ContractInline]

    fieldsets = (
        ("Identidad", {
            "fields": (("nombres", "apellidos"), ("dni", "tipo")),
        }),
        ("Datos laborales", {
            "fields": ("especialidad", "fecha_ingreso"),
        }),
        ("Contacto", {"fields": ("telefono", "email")}),
        ("Acceso al sistema", {
            "fields": ("user",),
            "description": (
                "Vincular al profesor con un usuario del sistema (opcional). "
                "Útil si el profesor va a operar el frontend con su propia cuenta."
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        # Prefetch para evitar N+1 en contadores y badges del changelist.
        return (
            super().get_queryset(request)
            .select_related("user")
            .prefetch_related("contracts", "aulas_titular", "aulas_auxiliar")
        )

    # ---- columnas del list_display ----

    @admin.display(description="")
    def avatar_mini(self, obj):
        """Avatar circular con la inicial. Color depende del tipo."""
        color = "#0d9488" if obj.tipo == "TITULAR" else "#6366f1"
        initial = (obj.nombres or "?")[:1].upper()
        return format_html(
            '<span style="display:inline-flex;width:32px;height:32px;'
            'border-radius:50%;background:{};color:#fff;align-items:center;'
            'justify-content:center;font-weight:700;font-size:13px">{}</span>',
            color, initial,
        )

    @admin.display(description="Nombre completo", ordering="apellidos")
    def nombre_completo(self, obj):
        return f"{obj.apellidos}, {obj.nombres}"

    @admin.display(description="Tipo", ordering="tipo")
    def tipo_badge(self, obj):
        colors = {"TITULAR": "#0d9488", "AUXILIAR": "#6366f1"}
        return _badge(obj.get_tipo_display(),
                      colors.get(obj.tipo, "#6b7280"))

    @admin.display(description="Contratos")
    def contratos_activos(self, obj):
        activos = sum(1 for c in obj.contracts.all() if c.activo)
        total = len(obj.contracts.all())
        if total == 0:
            return format_html('<span style="color:#ef4444">⚠ 0</span>')
        if activos == 0:
            return format_html(
                '<span style="color:#94a3b8">{} (sin activo)</span>', total,
            )
        return format_html(
            '<span style="color:#0d9488;font-weight:600">{} activo{}</span>'
            '<span style="color:#94a3b8"> / {}</span>',
            activos, "s" if activos != 1 else "", total,
        )

    @admin.display(description="Aulas")
    def aulas_a_cargo(self, obj):
        n_tit = len(obj.aulas_titular.all())
        n_aux = len(obj.aulas_auxiliar.all())
        total = n_tit + n_aux
        if total == 0:
            return format_html('<span style="color:#94a3b8">—</span>')
        # Distingue qué rol está cumpliendo (info visual sin abrir el aula).
        if obj.tipo == "TITULAR":
            return format_html(
                '<span style="color:#0d9488;font-weight:600">{} aula{}</span>',
                n_tit, "s" if n_tit != 1 else "",
            )
        return format_html(
            '<span style="color:#6366f1;font-weight:600">{} aula{}</span>',
            n_aux, "s" if n_aux != 1 else "",
        )

    @admin.display(description="WhatsApp", ordering="telefono")
    def telefono_link(self, obj):
        return _wa_link(obj.telefono)

    @admin.display(description="Email", ordering="email")
    def email_link(self, obj):
        return _mail_link(obj.email)


# ---------------------------------------------------------------------------
# TeacherContract admin
# ---------------------------------------------------------------------------

@admin.register(TeacherContract)
class TeacherContractAdmin(ModelAdmin):
    list_display = (
        "teacher_link",
        "tipo_badge",
        "sueldo_display",
        "periodo_display",
        "activo_badge",
        "pagos_count",
    )
    list_display_links = ("teacher_link",)
    list_filter = ()
    search_fields = (
        "teacher__nombres", "teacher__apellidos", "teacher__dni",
    )
    autocomplete_fields = ("teacher",)
    readonly_fields = ("created_at",)
    list_per_page = 30
    ordering = ("-activo", "-fecha_inicio")
    inlines = [PaymentInline]
    actions = ("accion_marcar_finalizado",)

    fieldsets = (
        ("Profesor", {"fields": ("teacher",)}),
        ("Condiciones", {
            "fields": (("tipo", "sueldo"), ("fecha_inicio", "fecha_fin"), "activo"),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at",),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("teacher")
            .prefetch_related("payments")
        )

    @admin.display(description="Profesor", ordering="teacher__apellidos")
    def teacher_link(self, obj):
        url = reverse("admin:teachers_teacher_change", args=[obj.teacher_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.teacher),
        )

    @admin.display(description="Tipo de contrato", ordering="tipo")
    def tipo_badge(self, obj):
        colors = {
            "TIEMPO_COMPLETO": "#10b981",
            "MEDIO_TIEMPO":    "#f59e0b",
            "POR_HORAS":       "#6366f1",
        }
        return _badge(obj.get_tipo_display(),
                      colors.get(obj.tipo, "#6b7280"))

    @admin.display(description="Sueldo", ordering="sueldo")
    def sueldo_display(self, obj):
        return format_html(
            '<strong>S/ {}</strong>',
            f"{obj.sueldo:,.2f}",
        )

    @admin.display(description="Periodo")
    def periodo_display(self, obj):
        inicio = obj.fecha_inicio.strftime("%d/%m/%Y") if obj.fecha_inicio else "—"
        if obj.fecha_fin:
            fin = obj.fecha_fin.strftime("%d/%m/%Y")
            return format_html('{} → {}', inicio, fin)
        return format_html('{} → <em style="color:#94a3b8">indefinido</em>', inicio)

    @admin.display(description="Estado", ordering="activo")
    def activo_badge(self, obj):
        if obj.activo:
            return _badge("Activo", "#10b981")
        return _badge("Finalizado", "#6b7280")

    @admin.display(description="Pagos")
    def pagos_count(self, obj):
        n = len(obj.payments.all())
        if n == 0:
            return format_html('<span style="color:#94a3b8">—</span>')
        return format_html(
            '<span style="color:#0d9488;font-weight:600">{}</span>', n,
        )

    @admin.action(description="Marcar contratos seleccionados como FINALIZADOS (fecha hoy)")
    def accion_marcar_finalizado(self, request, queryset):
        today = date.today()
        n = queryset.update(activo=False, fecha_fin=today)
        self.message_user(
            request,
            f"{n} contrato(s) marcado(s) como finalizado(s) con fecha {today.strftime('%d/%m/%Y')}.",
            messages.SUCCESS,
        )


# ---------------------------------------------------------------------------
# TeacherPayment admin
# ---------------------------------------------------------------------------

@admin.register(TeacherPayment)
class TeacherPaymentAdmin(ModelAdmin):
    list_display = (
        "teacher_link",
        "periodo_display",
        "monto_display",
        "metodo_badge",
        "fecha_pago",
        "comprobante",
    )
    list_display_links = ("teacher_link", "periodo_display")
    list_filter = ()
    search_fields = (
        "contract__teacher__nombres", "contract__teacher__apellidos",
        "contract__teacher__dni", "comprobante",
    )
    # Sacamos `contract` de autocomplete_fields para usar Select normal
    # con data-sueldo en cada option (el AutocompleteSelect carga via
    # AJAX y rompe el pre-llenado client-side).
    autocomplete_fields = ()
    readonly_fields = ("created_at",)
    date_hierarchy = "fecha_pago"
    list_per_page = 30
    ordering = ("-anio", "-mes", "contract__teacher__apellidos")

    # JS que pre-llena el campo `monto` con el sueldo del contrato
    # seleccionado. Respeta cualquier valor que el usuario haya tipeado
    # manualmente (no sobrescribe, solo llena si está vacío).
    class Media:
        js = ("admin/js/teacher_payment_autofill.js",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Inyecta `data-sueldo` en cada option del select de `contract`
        para que el JS del Media class lo lea al cambiar la selección.

        Performance: 1 query para cargar todos los sueldos en un dict,
        luego lookups O(1) en cada option. Sin N+1.
        """
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "contract":
            sueldos = {
                str(c.pk): str(c.sueldo)
                for c in TeacherContract.objects.all()
            }
            original_widget = formfield.widget
            original_create = original_widget.create_option

            def create_option_with_sueldo(name, value, label, selected,
                                          index, subindex=None, attrs=None):
                option = original_create(
                    name, value, label, selected, index, subindex, attrs,
                )
                actual_pk = getattr(value, "value", value) if value else None
                if actual_pk:
                    sueldo = sueldos.get(str(actual_pk))
                    if sueldo:
                        option["attrs"]["data-sueldo"] = sueldo
                return option

            original_widget.create_option = create_option_with_sueldo
        return formfield

    fieldsets = (
        ("Contrato", {"fields": ("contract",)}),
        ("Periodo del pago", {"fields": (("mes", "anio"),)}),
        ("Detalles", {
            "fields": ("monto", "fecha_pago", "metodo_pago", "comprobante"),
        }),
        ("Observaciones", {"fields": ("observaciones",)}),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at",),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("contract", "contract__teacher")
        )

    @admin.display(description="Profesor", ordering="contract__teacher__apellidos")
    def teacher_link(self, obj):
        teacher = obj.contract.teacher
        url = reverse("admin:teachers_teacher_change", args=[teacher.id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(teacher),
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

    @admin.display(description="Método", ordering="metodo_pago")
    def metodo_badge(self, obj):
        colors = {
            "TRANSFERENCIA": "#3b82f6",
            "EFECTIVO":      "#10b981",
            "DEPOSITO":      "#8b5cf6",
        }
        return _badge(obj.get_metodo_pago_display(),
                      colors.get(obj.metodo_pago, "#6b7280"))
