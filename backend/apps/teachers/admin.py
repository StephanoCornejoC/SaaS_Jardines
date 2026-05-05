from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline

from .models import Teacher, TeacherContract, TeacherPayment


class PaymentInline(TabularInline):
    model = TeacherPayment
    extra = 0
    fields = ("mes", "anio", "monto", "fecha_pago", "metodo_pago", "comprobante")


class ContractInline(TabularInline):
    model = TeacherContract
    extra = 0
    fields = ("tipo", "sueldo", "fecha_inicio", "fecha_fin", "activo")
    show_change_link = True


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    list_display = ("dni", "apellidos", "nombres", "especialidad", "telefono", "email", "fecha_ingreso")
    list_display_links = ("dni", "apellidos")
    list_filter = ("especialidad",)
    search_fields = ("dni", "nombres", "apellidos", "email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("apellidos", "nombres")
    list_per_page = 25
    inlines = [ContractInline]


@admin.register(TeacherContract)
class TeacherContractAdmin(ModelAdmin):
    list_display = ("teacher", "tipo", "sueldo", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("teacher__nombres", "teacher__apellidos")
    autocomplete_fields = ("teacher",)
    readonly_fields = ("created_at",)
    inlines = [PaymentInline]


@admin.register(TeacherPayment)
class TeacherPaymentAdmin(ModelAdmin):
    list_display = ("contract", "mes", "anio", "monto", "fecha_pago", "metodo_pago")
    list_filter = ("metodo_pago", "anio", "mes")
    search_fields = ("contract__teacher__nombres", "contract__teacher__apellidos")
    autocomplete_fields = ("contract",)
    readonly_fields = ("created_at",)
    date_hierarchy = "fecha_pago"
