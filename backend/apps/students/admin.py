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
    list_display_links = ("dni", "apellidos")
    list_filter = ("estado", "genero", "classroom")
    search_fields = ("dni", "nombres", "apellidos")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("apellidos", "nombres")
    list_per_page = 25
    inlines = [GuardianInline, MedicalRecordInline]
    fieldsets = (
        ("Datos personales", {
            "fields": ("dni", "nombres", "apellidos", "fecha_nacimiento", "genero", "foto"),
        }),
        ("Asignación", {
            "fields": ("classroom", "estado", "fecha_ingreso"),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(Guardian)
class GuardianAdmin(ModelAdmin):
    list_display = ("dni", "nombres", "apellidos", "parentesco", "telefono", "email", "es_principal", "student")
    list_display_links = ("dni", "nombres")
    list_filter = ("parentesco", "es_principal")
    search_fields = ("dni", "nombres", "apellidos", "telefono", "email", "student__nombres", "student__apellidos")
    autocomplete_fields = ("student",)
    list_per_page = 25


@admin.register(MedicalRecord)
class MedicalRecordAdmin(ModelAdmin):
    list_display = ("student", "tipo_sangre", "seguro", "contacto_emergencia_nombre", "contacto_emergencia_telefono")
    list_filter = ("tipo_sangre",)
    search_fields = ("student__nombres", "student__apellidos", "student__dni")
    autocomplete_fields = ("student",)
