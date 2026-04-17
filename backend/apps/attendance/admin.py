from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ("student", "classroom", "fecha", "estado", "registrado_por")
    list_filter = ("estado", "fecha", "classroom")
    search_fields = ("student__nombres", "student__apellidos")
    readonly_fields = ("created_at", "registrado_por")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
