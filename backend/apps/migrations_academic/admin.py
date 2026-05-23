"""Admin de la app migrations_academic.

Diseño:
  El cierre de año académico es un proceso delicado: mueve a todos los
  alumnos al siguiente nivel y los que cumplen 6 años pasan a "Egresado".
  El admin debe ser claramente de SOLO LECTURA — la migración real se
  dispara desde el frontend (Migración anual) con confirmación.

  Decisiones:
  - Badge de status (Preview / Ejecutado / Rollback).
  - Periodo "2025 → 2026" con flecha.
  - Contador de alumnos migrados destacado.
  - Inline read-only de detalles de migración con links a alumnos.
  - Sin add/change permissions: las migraciones son artefactos del sistema.
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from django.urls import reverse
from django.utils.html import format_html

from .models import AcademicMigration, MigrationDetail


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


class MigrationDetailInline(TabularInline):
    """Detalles de la migración mostrados dentro del cambio de AcademicMigration."""
    model = MigrationDetail
    extra = 0
    fields = (
        "student", "aula_origen", "aula_destino",
        "estado_anterior", "estado_nuevo",
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = False
    verbose_name_plural = "Alumnos migrados"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AcademicMigration)
class AcademicMigrationAdmin(ModelAdmin):
    list_display = (
        "fecha_display",
        "periodo_display",
        "total_migrados_display",
        "status_badge",
        "ejecutado_por",
    )
    list_display_links = ("periodo_display",)
    list_filter = ()
    search_fields = ("anio_origen", "anio_destino", "observaciones")
    readonly_fields = (
        "anio_origen", "anio_destino",
        "ejecutado_por", "fecha", "total_migrados",
        "status", "observaciones",
    )
    inlines = [MigrationDetailInline]
    ordering = ("-fecha",)
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("ejecutado_por")

    def has_add_permission(self, request):
        # La migración real se ejecuta desde el endpoint dedicado del
        # frontend (Migración anual). El admin es solo lectura para
        # auditoría.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Solo el superadmin del Hub puede borrar registros de migración
        # en caso de cierre erróneo (raro).
        return super().has_delete_permission(request, obj)

    # ---- columnas ----

    @admin.display(description="Fecha", ordering="-fecha")
    def fecha_display(self, obj):
        if not obj.fecha:
            return "—"
        return format_html(
            '<span>{}</span><br>'
            '<span style="color:#94a3b8;font-size:11px">{}</span>',
            obj.fecha.strftime("%d/%m/%Y"),
            obj.fecha.strftime("%H:%M"),
        )

    @admin.display(description="Periodo")
    def periodo_display(self, obj):
        return format_html(
            '<strong>{}</strong> '
            '<span style="color:#94a3b8">→</span> '
            '<strong style="color:#0d9488">{}</strong>',
            obj.anio_origen, obj.anio_destino,
        )

    @admin.display(description="Alumnos migrados", ordering="-total_migrados")
    def total_migrados_display(self, obj):
        if obj.total_migrados == 0:
            return format_html('<span style="color:#94a3b8">—</span>')
        return format_html(
            '<strong style="color:#0d9488;font-size:13px">{}</strong>'
            '<span style="color:#94a3b8"> alumno{}</span>',
            obj.total_migrados, "s" if obj.total_migrados != 1 else "",
        )

    @admin.display(description="Estado", ordering="status")
    def status_badge(self, obj):
        colors = {
            "PREVIEW":   "#94a3b8",  # gris: simulación
            "EJECUTADO": "#10b981",  # verde: aplicado
            "ROLLBACK":  "#ef4444",  # rojo: revertido
        }
        return _badge(obj.get_status_display(),
                      colors.get(obj.status, "#6b7280"))


@admin.register(MigrationDetail)
class MigrationDetailAdmin(ModelAdmin):
    list_display = (
        "student_link",
        "migration_link",
        "aulas_display",
        "estado_anterior",
        "estado_nuevo",
    )
    list_display_links = ("student_link",)
    list_filter = ()
    search_fields = (
        "student__nombres", "student__apellidos", "student__dni",
        "aula_origen__nombre", "aula_destino__nombre",
    )
    readonly_fields = (
        "migration", "student",
        "aula_origen", "aula_destino",
        "estado_anterior", "estado_nuevo",
    )
    list_per_page = 50

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("student", "migration", "aula_origen", "aula_destino")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ---- columnas ----

    @admin.display(description="Alumno", ordering="student__apellidos")
    def student_link(self, obj):
        url = reverse("admin:students_student_change", args=[obj.student_id])
        return format_html(
            '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
            url, str(obj.student),
        )

    @admin.display(description="Migración")
    def migration_link(self, obj):
        url = reverse(
            "admin:migrations_academic_academicmigration_change",
            args=[obj.migration_id],
        )
        return format_html(
            '<a href="{}" style="color:#94a3b8">{} → {}</a>',
            url, obj.migration.anio_origen, obj.migration.anio_destino,
        )

    @admin.display(description="Aulas (origen → destino)")
    def aulas_display(self, obj):
        origen = obj.aula_origen.nombre if obj.aula_origen_id else "—"
        destino = obj.aula_destino.nombre if obj.aula_destino_id else "—"
        return format_html(
            '<span style="color:#94a3b8">{}</span>'
            ' <span style="color:#0d9488">→</span> '
            '<strong>{}</strong>',
            origen, destino,
        )
