"""Admin de la app dashboard.

Diseño:
  `DashboardMetric` guarda un snapshot diario de las métricas clave del
  jardín (alumnos, profesores, balance, % morosidad, % asistencia). Se
  calcula via `dashboard.services.calculate_daily_metrics()` y queda
  como histórico read-only para auditar tendencias.

  Decisiones:
  - Read-only total: no se crea ni se edita desde el admin (son artefactos
    del cron diario).
  - KPIs con color: ingresos verdes, egresos rojos, balance dinámico.
  - Barras mini para % morosidad y % asistencia con código de color.
  - Date_hierarchy por fecha para navegar el histórico.
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html

from .models import DashboardMetric


def _bar(pct, color):
    """Barra mini de progreso 0-100 con el color dado."""
    pct_visual = min(max(int(pct), 0), 100)
    return format_html(
        '<div style="display:flex;align-items:center;gap:8px;min-width:130px">'
        '  <div style="flex:1;height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden">'
        '    <div style="width:{}%;height:100%;background:{}"></div>'
        '  </div>'
        '  <span style="font-size:12px;color:#475569;font-weight:600;white-space:nowrap">'
        '    {}%'
        '  </span>'
        '</div>',
        pct_visual, color, f"{pct:.1f}",
    )


@admin.register(DashboardMetric)
class DashboardMetricAdmin(ModelAdmin):
    list_display = (
        "fecha",
        "alumnos_y_profes",
        "ingresos_display",
        "egresos_display",
        "balance_display",
        "morosidad_bar",
        "asistencia_bar",
    )
    list_display_links = ("fecha",)
    list_filter = ()
    search_fields = ("fecha",)
    readonly_fields = (
        "fecha",
        "total_alumnos",
        "total_profesores",
        "alumnos_por_nivel",
        "ingresos_mes",
        "egresos_mes",
        "balance_mes",
        "porcentaje_morosidad",
        "porcentaje_asistencia",
        "created_at",
    )
    ordering = ("-fecha",)
    list_per_page = 30
    date_hierarchy = "fecha"

    fieldsets = (
        ("Día", {"fields": ("fecha",)}),
        ("Personas", {
            "fields": (("total_alumnos", "total_profesores"), "alumnos_por_nivel"),
        }),
        ("Finanzas del mes", {
            "fields": (("ingresos_mes", "egresos_mes"), "balance_mes"),
        }),
        ("Indicadores", {
            "fields": (("porcentaje_morosidad", "porcentaje_asistencia"),),
        }),
        ("Auditoría", {"classes": ("collapse",), "fields": ("created_at",)}),
    )

    def has_add_permission(self, request):
        # Las métricas las genera `calculate_daily_metrics` (cron diario).
        # NO se crean a mano.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Stephano puede borrar snapshots viejos si la tabla crece. Mantener
        # borrado disponible es razonable porque son derivados.
        return super().has_delete_permission(request, obj)

    # ---- columnas ----

    @admin.display(description="Alumnos / Profesores")
    def alumnos_y_profes(self, obj):
        return format_html(
            '<strong style="color:#0d9488">{}</strong>'
            '<span style="color:#94a3b8"> alumnos · </span>'
            '<strong style="color:#6366f1">{}</strong>'
            '<span style="color:#94a3b8"> profes</span>',
            obj.total_alumnos, obj.total_profesores,
        )

    @admin.display(description="Ingresos mes", ordering="-ingresos_mes")
    def ingresos_display(self, obj):
        return format_html(
            '<span style="color:#10b981;font-weight:600">+S/ {}</span>',
            f"{obj.ingresos_mes:,.2f}",
        )

    @admin.display(description="Egresos mes", ordering="-egresos_mes")
    def egresos_display(self, obj):
        return format_html(
            '<span style="color:#ef4444;font-weight:600">-S/ {}</span>',
            f"{obj.egresos_mes:,.2f}",
        )

    @admin.display(description="Balance mes", ordering="-balance_mes")
    def balance_display(self, obj):
        if obj.balance_mes > 0:
            color, sign = "#10b981", "+"
        elif obj.balance_mes < 0:
            color, sign = "#ef4444", ""
        else:
            color, sign = "#6b7280", ""
        return format_html(
            '<strong style="color:{};font-size:13px">{}S/ {}</strong>',
            color, sign, f"{obj.balance_mes:,.2f}",
        )

    @admin.display(description="% Morosidad", ordering="porcentaje_morosidad")
    def morosidad_bar(self, obj):
        # Más alta es peor: rojo si >20%, ámbar si 10-20%, verde si <10%.
        pct = float(obj.porcentaje_morosidad)
        if pct >= 20:
            color = "#ef4444"
        elif pct >= 10:
            color = "#f59e0b"
        else:
            color = "#10b981"
        return _bar(pct, color)

    @admin.display(description="% Asistencia", ordering="-porcentaje_asistencia")
    def asistencia_bar(self, obj):
        # Más alta es mejor: verde si >90%, ámbar si 75-90%, rojo si <75%.
        pct = float(obj.porcentaje_asistencia)
        if pct >= 90:
            color = "#10b981"
        elif pct >= 75:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        return _bar(pct, color)
