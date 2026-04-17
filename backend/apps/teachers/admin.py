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
    list_display = ("dni", "apellidos", "nombres", "especialidad", "activo", "fecha_ingreso")
    list_filter = ("activo", "especialidad")
    search_fields = ("dni", "nombres", "apellidos")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("apellidos", "nombres")
    inlines = [ContractInline]


@admin.register(TeacherContract)
class TeacherContractAdmin(ModelAdmin):
    list_display = ("teacher", "tipo", "sueldo", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("teacher__nombres", "teacher__apellidos")
    readonly_fields = ("created_at",)
    inlines = [PaymentInline]
