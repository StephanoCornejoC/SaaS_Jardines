from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Classroom


@admin.register(Classroom)
class ClassroomAdmin(ModelAdmin):
    list_display = (
        "nombre",
        "nivel_edad",
        "capacidad",
        "alumnos_count",
        "profesor_titular",
        "profesor_auxiliar",
        "anio_escolar",
        "activo",
    )
    list_filter = ("nivel_edad", "anio_escolar", "activo")
    search_fields = ("nombre", "profesor_titular__apellidos", "profesor_auxiliar__apellidos")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("anio_escolar", "nivel_edad", "nombre")
