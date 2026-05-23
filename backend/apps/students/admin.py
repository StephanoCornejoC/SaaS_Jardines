"""Admin de la app students.

Diseño:
  Pulido para que Stephano pueda hacer CRUD completo de alumnos desde el
  admin Django (modo Operar de un jardín), sin tener que entrar al frontend.

  Decisiones:
  - Foto preview en list_display y en el change form.
  - Badges de color para estado, género, parentesco, tipo de sangre.
  - Links externos clickeables: wa.me (WhatsApp del apoderado / contacto
    emergencia), mailto (email del apoderado), enlace al aula.
  - Search amplio: cubre DNI y nombre del alumno + nombre/teléfono del
    apoderado, así si la directora busca por el apellido del padre lo
    encuentra igual.
  - Acciones bulk: marcar como retirado/egresado, restaurar a activo
    (operaciones masivas que la directora puede hacer al cierre del año).
  - Inlines: Guardian + MedicalRecord directamente en el form del alumno.
"""

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, TabularInline
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Guardian, MedicalRecord, Student


# ---------------------------------------------------------------------------
# Helpers de UI compartidos
# ---------------------------------------------------------------------------

_BADGE_BASE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE_BASE.format(bg=bg), text)


def _wa_link(telefono):
    """Devuelve un <a> que abre wa.me con el teléfono (sin formato)."""
    if not telefono:
        return "—"
    # Sanitizar: dejar solo dígitos. Si empieza con 9, asumimos celular Perú (+51).
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


# ---------------------------------------------------------------------------
# Inlines (van adentro del form del alumno)
# ---------------------------------------------------------------------------

class GuardianInline(TabularInline):
    model = Guardian
    extra = 0
    fields = (
        "dni", "nombres", "apellidos", "parentesco",
        "telefono", "email", "es_principal",
    )
    classes = ("collapse-open",)
    verbose_name = "Apoderado"
    verbose_name_plural = "Apoderados del alumno"


class MedicalRecordInline(TabularInline):
    model = MedicalRecord
    extra = 0
    max_num = 1
    fields = (
        "tipo_sangre", "alergias", "seguro", "hospital_referencia",
        "contacto_emergencia_nombre", "contacto_emergencia_telefono",
        "observaciones",
    )
    verbose_name = "Ficha médica"
    verbose_name_plural = "Ficha médica"


# ---------------------------------------------------------------------------
# Student admin
# ---------------------------------------------------------------------------

@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = (
        "foto_mini",
        "dni",
        "nombre_completo",
        "edad_display",
        "genero_badge",
        "classroom_link",
        "apoderados_count",
        "tiene_ficha_medica",
        "estado_badge",
        "fecha_ingreso",
    )
    list_display_links = ("dni", "nombre_completo")
    # Filtros laterales deshabilitados a pedido de Stephano — el search y los
    # badges en list_display cubren los casos reales de búsqueda.
    list_filter = ()
    search_fields = (
        "dni", "nombres", "apellidos",
        "apoderados__nombres", "apoderados__apellidos",
        "apoderados__telefono", "apoderados__dni",
    )
    ordering = ("apellidos", "nombres")
    list_per_page = 30
    date_hierarchy = "fecha_ingreso"
    readonly_fields = ("created_at", "updated_at", "foto_preview", "edad_display")
    inlines = [GuardianInline, MedicalRecordInline]
    actions = ("accion_marcar_retirado", "accion_marcar_egresado",
               "accion_restaurar_activo")

    fieldsets = (
        ("Datos personales", {
            "fields": (
                ("nombres", "apellidos"),
                ("dni", "fecha_nacimiento", "edad_display"),
                ("genero",),
                ("foto", "foto_preview"),
            ),
        }),
        ("Asignación escolar", {
            "fields": (("classroom", "estado"), "fecha_ingreso", "ficha_matricula"),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        # select_related al aula y prefetch a apoderados / ficha_medica
        # evita N+1 en el changelist con badges y contadores.
        qs = super().get_queryset(request).select_related("classroom")
        return qs.prefetch_related("apoderados", "ficha_medica")

    # ---- columnas del list_display ----

    @admin.display(description="")
    def foto_mini(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="width:32px;height:32px;border-radius:50%;'
                'object-fit:cover;border:1px solid #ccc" alt="foto">',
                obj.foto.url,
            )
        # Fallback: inicial sobre círculo coloreado
        color = "#f472b6" if obj.genero == "F" else "#60a5fa"
        return format_html(
            '<span style="display:inline-flex;width:32px;height:32px;'
            'border-radius:50%;background:{};color:#fff;align-items:center;'
            'justify-content:center;font-weight:700;font-size:12px">{}</span>',
            color, (obj.nombres or "?")[:1].upper(),
        )

    @admin.display(description="Foto", )
    def foto_preview(self, obj):
        if not obj.foto:
            return mark_safe('<em style="color:#888">Sin foto cargada</em>')
        return format_html(
            '<img src="{}" style="max-width:200px;max-height:200px;'
            'border-radius:8px;border:1px solid #ddd">',
            obj.foto.url,
        )

    @admin.display(description="Nombre completo", ordering="apellidos")
    def nombre_completo(self, obj):
        return f"{obj.apellidos}, {obj.nombres}"

    @admin.display(description="Edad")
    def edad_display(self, obj):
        if not obj.fecha_nacimiento:
            return "—"
        e = obj.edad
        return format_html('<strong>{} años</strong>', e)

    @admin.display(description="Género", ordering="genero")
    def genero_badge(self, obj):
        if obj.genero == "F":
            return _badge("F", "#f472b6")
        if obj.genero == "M":
            return _badge("M", "#60a5fa")
        return "—"

    @admin.display(description="Aula", ordering="classroom__nombre")
    def classroom_link(self, obj):
        if not obj.classroom:
            return format_html('<span style="color:#94a3b8">sin aula</span>')
        url = reverse("admin:classrooms_classroom_change", args=[obj.classroom_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{} ({}a)</a>',
            url, obj.classroom.nombre, obj.classroom.nivel_edad,
        )

    @admin.display(description="Apod.")
    def apoderados_count(self, obj):
        n = obj.apoderados.count()
        if n == 0:
            return format_html('<span style="color:#ef4444">⚠ 0</span>')
        return format_html(
            '<span style="color:#0d9488;font-weight:600">{}</span>', n,
        )

    @admin.display(description="Ficha méd.")
    def tiene_ficha_medica(self, obj):
        try:
            obj.ficha_medica
            return format_html('<span style="color:#10b981">✓</span>')
        except MedicalRecord.DoesNotExist:
            return format_html('<span style="color:#ef4444">—</span>')

    @admin.display(description="Estado", ordering="estado")
    def estado_badge(self, obj):
        colors = {
            "ACTIVO":    "#10b981",
            "RETIRADO":  "#f59e0b",
            "EGRESADO":  "#3b82f6",
            "ELIMINADO": "#6b7280",
        }
        return _badge(obj.get_estado_display(),
                      colors.get(obj.estado, "#6b7280"))

    # ---- acciones bulk ----

    @admin.action(description="Marcar como RETIRADO")
    def accion_marcar_retirado(self, request, queryset):
        n = queryset.update(estado=Student.Estado.RETIRADO)
        self.message_user(request,
                          f"{n} alumno(s) marcado(s) como Retirado.",
                          messages.SUCCESS)

    @admin.action(description="Marcar como EGRESADO (fin del año)")
    def accion_marcar_egresado(self, request, queryset):
        n = queryset.update(estado=Student.Estado.EGRESADO)
        self.message_user(request,
                          f"{n} alumno(s) marcado(s) como Egresado.",
                          messages.SUCCESS)

    @admin.action(description="Restaurar a ACTIVO")
    def accion_restaurar_activo(self, request, queryset):
        n = queryset.update(estado=Student.Estado.ACTIVO)
        self.message_user(request,
                          f"{n} alumno(s) restaurado(s) a Activo.",
                          messages.SUCCESS)


# ---------------------------------------------------------------------------
# Guardian admin
# ---------------------------------------------------------------------------

@admin.register(Guardian)
class GuardianAdmin(ModelAdmin):
    list_display = (
        "principal_badge",
        "dni",
        "nombre_completo",
        "parentesco_badge",
        "telefono_link",
        "email_link",
        "student_link",
    )
    list_display_links = ("dni", "nombre_completo")
    list_filter = ()
    search_fields = (
        "dni", "nombres", "apellidos", "telefono", "email",
        "student__nombres", "student__apellidos", "student__dni",
    )
    autocomplete_fields = ("student",)
    list_per_page = 30
    ordering = ("-es_principal", "apellidos", "nombres")
    actions = ("accion_marcar_principal",)

    fieldsets = (
        ("Alumno", {"fields": ("student", "parentesco", "es_principal")}),
        ("Datos personales", {
            "fields": (("nombres", "apellidos"), "dni"),
        }),
        ("Contacto", {"fields": ("telefono", "email")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student")

    @admin.display(description="", ordering="-es_principal")
    def principal_badge(self, obj):
        if obj.es_principal:
            return format_html(
                '<span title="Apoderado principal" '
                'style="color:#f59e0b;font-size:18px">★</span>'
            )
        return format_html(
            '<span style="color:#cbd5e1;font-size:18px">☆</span>'
        )

    @admin.display(description="Nombre completo", ordering="apellidos")
    def nombre_completo(self, obj):
        return f"{obj.apellidos}, {obj.nombres}"

    @admin.display(description="Parentesco", ordering="parentesco")
    def parentesco_badge(self, obj):
        colors = {
            "PADRE": "#3b82f6",
            "MADRE": "#ec4899",
            "TUTOR": "#8b5cf6",
            "OTRO":  "#6b7280",
        }
        return _badge(obj.get_parentesco_display(),
                      colors.get(obj.parentesco, "#6b7280"))

    @admin.display(description="WhatsApp", ordering="telefono")
    def telefono_link(self, obj):
        return _wa_link(obj.telefono)

    @admin.display(description="Email", ordering="email")
    def email_link(self, obj):
        return _mail_link(obj.email)

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.action(description="Marcar como apoderado PRINCIPAL")
    def accion_marcar_principal(self, request, queryset):
        # Al marcar uno como principal, desmarcamos los demás del mismo
        # alumno (regla de negocio: solo 1 principal por alumno).
        affected = 0
        for guardian in queryset:
            Guardian.objects.filter(
                student_id=guardian.student_id, es_principal=True,
            ).exclude(pk=guardian.pk).update(es_principal=False)
            if not guardian.es_principal:
                guardian.es_principal = True
                guardian.save(update_fields=["es_principal"])
            affected += 1
        self.message_user(request,
                          f"{affected} apoderado(s) marcado(s) como principal.",
                          messages.SUCCESS)


# ---------------------------------------------------------------------------
# MedicalRecord admin
# ---------------------------------------------------------------------------

@admin.register(MedicalRecord)
class MedicalRecordAdmin(ModelAdmin):
    list_display = (
        "student_link",
        "tipo_sangre_badge",
        "alergias_warning",
        "seguro",
        "contacto_emergencia_nombre",
        "contacto_emergencia_link",
    )
    list_filter = ()
    search_fields = (
        "student__nombres", "student__apellidos", "student__dni",
        "contacto_emergencia_nombre", "alergias",
    )
    autocomplete_fields = ("student",)
    list_per_page = 30

    fieldsets = (
        ("Alumno", {"fields": ("student",)}),
        ("Datos médicos", {
            "fields": ("tipo_sangre", "alergias", "seguro", "hospital_referencia"),
        }),
        ("Contacto de emergencia", {
            "fields": ("contacto_emergencia_nombre", "contacto_emergencia_telefono"),
        }),
        ("Observaciones", {"fields": ("observaciones",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student")

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Tipo sangre", ordering="tipo_sangre")
    def tipo_sangre_badge(self, obj):
        return _badge(obj.tipo_sangre, "#dc2626")

    @admin.display(description="Alergias")
    def alergias_warning(self, obj):
        if not obj.alergias:
            return format_html('<span style="color:#94a3b8">sin alergias</span>')
        # Truncar para no romper layout
        texto = obj.alergias.strip()
        if len(texto) > 40:
            texto = texto[:40] + "…"
        return format_html(
            '<span style="color:#dc2626;font-weight:600" title="{}">⚠ {}</span>',
            obj.alergias, texto,
        )

    @admin.display(description="Contacto", ordering="contacto_emergencia_telefono")
    def contacto_emergencia_link(self, obj):
        return _wa_link(obj.contacto_emergencia_telefono)
