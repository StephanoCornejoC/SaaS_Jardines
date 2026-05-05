from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import CashCategory, CashTransaction, MonthlyClosure


@admin.register(CashCategory)
class CashCategoryAdmin(ModelAdmin):
    list_display = ("nombre", "tipo", "es_sistema", "activo")
    list_filter = ("tipo", "activo", "es_sistema")
    search_fields = ("nombre",)
    readonly_fields = ("created_at",)
    list_per_page = 25


@admin.register(CashTransaction)
class CashTransactionAdmin(ModelAdmin):
    list_display = ("descripcion", "categoria", "monto", "tipo", "fecha", "creado_por")
    list_display_links = ("descripcion",)
    list_filter = ("tipo", "categoria", "fecha")
    search_fields = ("descripcion",)
    autocomplete_fields = ("categoria",)
    readonly_fields = ("created_at", "updated_at", "creado_por")
    ordering = ("-fecha",)
    list_per_page = 30
    date_hierarchy = "fecha"


@admin.register(MonthlyClosure)
class MonthlyClosureAdmin(ModelAdmin):
    list_display = ("mes", "anio", "total_ingresos", "total_egresos", "balance", "cerrado_por")
    list_filter = ("anio",)
    readonly_fields = (
        "mes",
        "anio",
        "total_ingresos",
        "total_egresos",
        "balance",
        "cerrado_por",
        "fecha_cierre",
    )
