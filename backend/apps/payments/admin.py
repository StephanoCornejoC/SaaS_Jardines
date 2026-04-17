from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import MonthlyFee, Payment


@admin.register(MonthlyFee)
class MonthlyFeeAdmin(ModelAdmin):
    list_display = ("student", "anio_escolar", "monto_mensual", "dia_vencimiento")
    list_filter = ("anio_escolar",)
    search_fields = ("student__nombres", "student__apellidos", "student__dni")
    readonly_fields = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        "student",
        "mes",
        "anio",
        "monto",
        "estado",
        "fecha_vencimiento",
        "fecha_pago",
        "metodo_pago",
    )
    list_filter = ("estado", "anio", "mes", "metodo_pago")
    search_fields = ("student__nombres", "student__apellidos", "student__dni", "comprobante")
    readonly_fields = ("created_at", "updated_at", "registrado_por")
    ordering = ("-anio", "-mes")
