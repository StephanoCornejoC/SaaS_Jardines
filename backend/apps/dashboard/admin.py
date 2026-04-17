from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import DashboardMetric


@admin.register(DashboardMetric)
class DashboardMetricAdmin(ModelAdmin):
    list_display = (
        "fecha",
        "total_alumnos",
        "total_profesores",
        "ingresos_mes",
        "egresos_mes",
        "balance_mes",
        "porcentaje_morosidad",
        "porcentaje_asistencia",
    )
    list_filter = ("fecha",)
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
