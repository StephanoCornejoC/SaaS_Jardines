from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Communication


@admin.register(Communication)
class CommunicationAdmin(ModelAdmin):
    list_display = ("titulo", "tipo", "classroom", "enviado", "fecha_envio", "enviado_por")
    list_display_links = ("titulo",)
    list_filter = ("tipo", "enviado")
    search_fields = ("titulo", "contenido")
    autocomplete_fields = ("classroom",)
    readonly_fields = ("created_at", "updated_at", "fecha_envio", "enviado", "enviado_por")
    ordering = ("-created_at",)
    list_per_page = 25
