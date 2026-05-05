from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = (
        "student",
        "classroom",
        "anio_escolar",
        "costo_matricula",
        "fecha_matricula",
    )
    list_display_links = ("student",)
    list_filter = ("anio_escolar", "classroom")
    search_fields = ("student__nombres", "student__apellidos", "student__dni")
    autocomplete_fields = ("student", "classroom")
    readonly_fields = ("created_at", "updated_at", "created_by")
    ordering = ("-anio_escolar", "student__apellidos")
    list_per_page = 30
    date_hierarchy = "fecha_matricula"
