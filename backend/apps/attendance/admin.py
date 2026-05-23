"""Admin de la app attendance.

Diseño:
  Pulido para que la directora vea el registro diario de asistencia
  con badges claros del estado y links a alumno/aula.

  Decisiones:
  - Badge de estado coloreado (verde Presente, rojo Ausente, ámbar
    Tardanza, azul Justificado).
  - Links clickeables al alumno y al aula.
  - Fecha formateada DD/MM/YYYY.
  - Date_hierarchy por fecha para navegación rápida.
  - Sin list_filter (consistente con el resto del admin).
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Attendance


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = (
        "fecha_display",
        "student_link",
        "classroom_link",
        "estado_badge",
        "observaciones_short",
        "registrado_por",
    )
    list_display_links = ("student_link",)
    list_filter = ()
    search_fields = (
        "student__nombres", "student__apellidos", "student__dni",
        "classroom__nombre",
    )
    autocomplete_fields = ("student", "classroom")
    readonly_fields = ("created_at", "registrado_por")
    date_hierarchy = "fecha"
    ordering = ("-fecha", "student__apellidos")
    list_per_page = 50

    fieldsets = (
        ("Asistencia", {
            "fields": (("student", "classroom"), ("fecha", "estado")),
        }),
        ("Observaciones", {"fields": ("observaciones",)}),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("registrado_por", "created_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("student", "classroom", "registrado_por")
        )

    # ---- columnas ----

    @admin.display(description="Fecha", ordering="-fecha")
    def fecha_display(self, obj):
        if not obj.fecha:
            return "—"
        return format_html(
            '<strong>{}</strong>', obj.fecha.strftime("%d/%m/%Y"),
        )

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Aula", ordering="classroom__nombre")
    def classroom_link(self, obj):
        url = reverse("admin:classrooms_classroom_change", args=[obj.classroom_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, obj.classroom.nombre,
        )

    @admin.display(description="Estado", ordering="estado")
    def estado_badge(self, obj):
        colors = {
            "PRESENTE":    "#10b981",
            "AUSENTE":     "#ef4444",
            "TARDANZA":    "#f59e0b",
            "JUSTIFICADO": "#3b82f6",
        }
        return _badge(obj.get_estado_display(),
                      colors.get(obj.estado, "#6b7280"))

    @admin.display(description="Observaciones")
    def observaciones_short(self, obj):
        if not obj.observaciones:
            return format_html('<span style="color:#94a3b8">—</span>')
        texto = obj.observaciones.strip()
        if len(texto) > 50:
            texto = texto[:50] + "…"
        return format_html(
            '<span title="{}">{}</span>', obj.observaciones, texto,
        )
