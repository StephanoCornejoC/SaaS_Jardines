from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ("asunto", "destinatario", "tipo", "enviado", "created_at")
    list_filter = ("tipo", "enviado")
    search_fields = ("destinatario", "asunto", "contenido")
    readonly_fields = (
        "destinatario",
        "asunto",
        "contenido",
        "tipo",
        "enviado",
        "error",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
