from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline

from .models import AcademicMigration, MigrationDetail


class MigrationDetailInline(TabularInline):
    model = MigrationDetail
    extra = 0
    readonly_fields = (
        "student",
        "aula_origen",
        "aula_destino",
        "estado_anterior",
        "estado_nuevo",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AcademicMigration)
class AcademicMigrationAdmin(ModelAdmin):
    list_display = (
        "anio_origen",
        "anio_destino",
        "total_migrados",
        "status",
        "ejecutado_por",
        "fecha",
    )
    list_filter = ("status", "anio_origen")
    readonly_fields = (
        "anio_origen",
        "anio_destino",
        "ejecutado_por",
        "fecha",
        "total_migrados",
        "status",
        "observaciones",
    )
    inlines = [MigrationDetailInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MigrationDetail)
class MigrationDetailAdmin(ModelAdmin):
    list_display = ("student", "aula_origen", "aula_destino", "estado_anterior", "estado_nuevo")
    list_filter = ("estado_nuevo",)
    readonly_fields = (
        "migration",
        "student",
        "aula_origen",
        "aula_destino",
        "estado_anterior",
        "estado_nuevo",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
