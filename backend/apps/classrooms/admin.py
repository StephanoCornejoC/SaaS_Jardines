"""Admin de la app classrooms.

Diseño:
  Pulido para que la directora gestione aulas con visión rápida del estado:
  cuántos alumnos tiene, qué tan llena está, qué profesores la atienden.

  Decisiones:
  - Avatar/inicial coloreada por nivel de edad (2/3/4/5 años).
  - Badge del nivel + barra de ocupación mini (verde si <70%, ámbar si
    70-90%, rojo si >90%).
  - Links a profesor titular/auxiliar; alerta visible si falta titular
    (es requerido por regla de negocio del SaaS).
  - Sin list_filter (consistente con students/teachers — el search +
    los badges visuales alcanzan).
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Classroom


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


# Color por nivel de edad — sale de la paleta del SaaS.
_NIVEL_COLOR = {
    2: "#f59e0b",  # ámbar
    3: "#10b981",  # verde
    4: "#3b82f6",  # azul
    5: "#8b5cf6",  # violeta
}


@admin.register(Classroom)
class ClassroomAdmin(ModelAdmin):
    list_display = (
        "icono_nivel",
        "nombre",
        "nivel_badge",
        "ocupacion_display",
        "profesor_titular_link",
        "profesor_auxiliar_link",
    )
    list_display_links = ("nombre",)
    list_filter = ()
    search_fields = (
        "nombre",
        "profesor_titular__nombres", "profesor_titular__apellidos",
        "profesor_auxiliar__nombres", "profesor_auxiliar__apellidos",
    )
    autocomplete_fields = ("profesor_titular", "profesor_auxiliar")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("nivel_edad", "nombre")
    list_per_page = 30

    fieldsets = (
        ("Identidad", {
            "fields": (("nombre", "nivel_edad"), "capacidad"),
        }),
        ("Personal docente", {
            "fields": ("profesor_titular", "profesor_auxiliar"),
            "description": (
                "El profesor titular es obligatorio. El auxiliar es opcional. "
                "Solo aparecen los profesores del tipo correcto en cada selector."
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("profesor_titular", "profesor_auxiliar")
            .prefetch_related("students")
        )

    # ---- columnas del list_display ----

    @admin.display(description="")
    def icono_nivel(self, obj):
        color = _NIVEL_COLOR.get(obj.nivel_edad, "#6b7280")
        return format_html(
            '<span style="display:inline-flex;width:32px;height:32px;'
            'border-radius:50%;background:{};color:#fff;align-items:center;'
            'justify-content:center;font-weight:700;font-size:13px">{}</span>',
            color, obj.nivel_edad,
        )

    @admin.display(description="Nivel", ordering="nivel_edad")
    def nivel_badge(self, obj):
        color = _NIVEL_COLOR.get(obj.nivel_edad, "#6b7280")
        return _badge(f"{obj.nivel_edad} años", color)

    @admin.display(description="Ocupación")
    def ocupacion_display(self, obj):
        """Cuenta alumnos / capacidad + barra mini con color según %.

        Usa `prefetch_related("students")` para evitar 1 query por aula
        en el changelist.
        """
        actuales = len(obj.students.all())
        cap = obj.capacidad or 0
        pct = int(round((actuales / cap) * 100)) if cap else 0

        # Color de la barra según ocupación
        if pct >= 90:
            bar_color = "#ef4444"  # rojo: sobre cupo
        elif pct >= 70:
            bar_color = "#f59e0b"  # ámbar: lleno
        else:
            bar_color = "#10b981"  # verde: disponible

        # Limitar visual al 100% si excede
        pct_visual = min(pct, 100)

        return format_html(
            '<div style="display:flex;align-items:center;gap:8px;min-width:140px">'
            '  <div style="flex:1;height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden">'
            '    <div style="width:{}%;height:100%;background:{}"></div>'
            '  </div>'
            '  <span style="font-size:12px;color:#475569;font-weight:600;white-space:nowrap">'
            '    {} / {}'
            '  </span>'
            '</div>',
            pct_visual, bar_color, actuales, cap,
        )

    @admin.display(description="Profesor titular", ordering="profesor_titular__apellidos")
    def profesor_titular_link(self, obj):
        if not obj.profesor_titular_id:
            return format_html(
                '<span style="color:#ef4444;font-weight:600">⚠ sin titular</span>'
            )
        url = reverse("admin:teachers_teacher_change", args=[obj.profesor_titular_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.profesor_titular),
        )

    @admin.display(description="Profesor auxiliar", ordering="profesor_auxiliar__apellidos")
    def profesor_auxiliar_link(self, obj):
        if not obj.profesor_auxiliar_id:
            return format_html('<span style="color:#94a3b8">—</span>')
        url = reverse("admin:teachers_teacher_change", args=[obj.profesor_auxiliar_id])
        return format_html(
            '<a href="{}" style="color:#6366f1;font-weight:600">{}</a>',
            url, str(obj.profesor_auxiliar),
        )
