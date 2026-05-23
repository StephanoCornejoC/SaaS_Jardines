"""Admin de la app enrollments.

Diseño:
  Pulido para que la directora vea de un vistazo qué alumnos están
  matriculados en cada año y aula.

  Decisiones:
  - Links clickeables al alumno y al aula.
  - Badge del año escolar (verde si es el año actual, gris si anterior).
  - Costo de matrícula formateado en S/.
  - Indicador del autor de la matrícula (quién la registró).
  - Sin list_filter (consistente con el resto del admin).
"""

from datetime import date

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Enrollment


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = (
        "anio_badge",
        "student_link",
        "classroom_link",
        "costo_display",
        "fecha_matricula",
        "created_by",
    )
    list_display_links = ("student_link",)
    list_filter = ()
    search_fields = (
        "student__nombres", "student__apellidos", "student__dni",
        "classroom__nombre",
    )
    autocomplete_fields = ("student", "classroom")
    readonly_fields = ("created_at", "updated_at", "created_by", "fecha_matricula")
    ordering = ("-anio_escolar", "student__apellidos")
    list_per_page = 30
    date_hierarchy = "fecha_matricula"

    fieldsets = (
        ("Matrícula", {
            "fields": (("student", "classroom"), ("anio_escolar", "costo_matricula")),
        }),
        ("Notas", {"fields": ("observaciones",)}),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("fecha_matricula", "created_by", "created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("student", "classroom", "created_by")
        )

    # ---- columnas ----

    @admin.display(description="Año", ordering="-anio_escolar")
    def anio_badge(self, obj):
        anio_actual = date.today().year
        if obj.anio_escolar == anio_actual:
            return _badge(str(obj.anio_escolar), "#10b981")  # verde año actual
        if obj.anio_escolar > anio_actual:
            return _badge(str(obj.anio_escolar), "#3b82f6")  # azul año futuro
        return _badge(str(obj.anio_escolar), "#94a3b8")      # gris anterior

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Aula", ordering="classroom__nombre")
    def classroom_link(self, obj):
        if not obj.classroom_id:
            return format_html('<span style="color:#94a3b8">sin aula</span>')
        url = reverse("admin:classrooms_classroom_change", args=[obj.classroom_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{} ({}a)</a>',
            url, obj.classroom.nombre, obj.classroom.nivel_edad,
        )

    @admin.display(description="Costo matrícula", ordering="costo_matricula")
    def costo_display(self, obj):
        return format_html('<strong>S/ {}</strong>', f"{obj.costo_matricula:,.2f}")
