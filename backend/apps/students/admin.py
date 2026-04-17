from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline

from .models import Guardian, MedicalRecord, Student


class GuardianInline(TabularInline):
    model = Guardian
    extra = 0
    fields = ("dni", "nombres", "apellidos", "telefono", "email", "parentesco", "es_principal")


class MedicalRecordInline(TabularInline):
    model = MedicalRecord
    extra = 0
    max_num = 1
    fields = (
        "tipo_sangre",
        "alergias",
        "seguro",
        "hospital_referencia",
        "contacto_emergencia_nombre",
        "contacto_emergencia_telefono",
        "observaciones",
    )


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ("dni", "apellidos", "nombres", "edad", "classroom", "estado", "fecha_ingreso")
    list_filter = ("estado", "genero", "classroom")
    search_fields = ("dni", "nombres", "apellidos")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("apellidos", "nombres")
    inlines = [GuardianInline, MedicalRecordInline]
