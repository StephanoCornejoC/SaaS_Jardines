from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ("nombre", "schema_name", "ruc", "plan", "activo", "created_at")
    list_filter = ("plan", "activo", "created_at")
    search_fields = ("nombre", "ruc", "schema_name", "email")
    readonly_fields = ("schema_name", "created_at", "updated_at")
    ordering = ("nombre",)


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)
