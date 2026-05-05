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
    )
    list_display_links = ("nombre",)
    list_filter = ("nivel_edad",)
    search_fields = ("nombre", "profesor_titular__apellidos", "profesor_auxiliar__apellidos")
    autocomplete_fields = ("profesor_titular", "profesor_auxiliar")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("nivel_edad", "nombre")
    list_per_page = 25
