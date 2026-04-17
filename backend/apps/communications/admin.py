from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Communication


@admin.register(Communication)
class CommunicationAdmin(ModelAdmin):
    list_display = ("titulo", "tipo", "classroom", "enviado", "fecha_envio", "enviado_por")
    list_filter = ("tipo", "enviado")
    search_fields = ("titulo", "contenido")
    readonly_fields = ("created_at", "updated_at", "fecha_envio", "enviado")
    ordering = ("-created_at",)
