from datetime import date

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Plan, PlatformCost, PlatformInvoice, TenantSubscription


# ============================================================================
# Plan
# ============================================================================

@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = (
        "nombre",
        "tipo_badge",
        "precio_mensual",
        "descripcion",
        "activo",
        "creado_at",
    )
    list_filter = ("activo", "es_promocional")
    list_editable = ("precio_mensual", "activo")
    search_fields = ("nombre", "descripcion")
    readonly_fields = ("creado_at", "actualizado_at")
    fieldsets = (
        (None, {"fields": ("nombre", "precio_mensual", "descripcion")}),
        ("Tipo", {"fields": ("es_promocional", "activo")}),
        ("Auditoría", {"classes": ("collapse",), "fields": ("creado_at", "actualizado_at")}),
    )

    @admin.display(description="Tipo", ordering="es_promocional")
    def tipo_badge(self, obj):
        if obj.es_promocional:
            return format_html(
                '<span style="background:#f59e0b;color:#fff;padding:2px 9px;'
                'border-radius:4px;font-size:11px;font-weight:600">Promocional</span>'
            )
        return format_html(
            '<span style="background:#0d9488;color:#fff;padding:2px 9px;'
            'border-radius:4px;font-size:11px;font-weight:600">Principal</span>'
        )


# ============================================================================
# TenantSubscription
# ============================================================================

@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(ModelAdmin):
    list_display = (
        "tenant_link",
        "plan",
        "precio_acordado",
        "fecha_alta",
        "trial_hasta",
        "dia_cobro",
        "proximo_cobro_display",
        "estado_badge",
    )
    list_filter = ("estado", "plan")
    search_fields = ("tenant__nombre", "tenant__ruc")
    autocomplete_fields = ("tenant", "plan")
    readonly_fields = ("creado_at", "actualizado_at", "proximo_cobro_display")
    list_per_page = 30

    fieldsets = (
        ("Jardín", {"fields": ("tenant", "plan", "precio_acordado")}),
        (
            "Periodo y cobro",
            {
                "fields": (
                    "fecha_alta",
                    "trial_hasta",
                    "dia_cobro",
                    "proximo_cobro_display",
                    "estado",
                )
            },
        ),
        ("Notas", {"fields": ("notas",)}),
        ("Auditoría", {"classes": ("collapse",), "fields": ("creado_at", "actualizado_at")}),
    )

    @admin.display(description="Jardín", ordering="tenant__nombre")
    def tenant_link(self, obj):
        url = reverse("admin:tenants_tenant_change", args=[obj.tenant_id])
        return format_html('<a href="{}">{}</a>', url, obj.tenant.nombre)

    @admin.display(description="Próximo cobro")
    def proximo_cobro_display(self, obj):
        if not obj.pk:
            return "—"
        try:
            d = obj.proximo_cobro
        except Exception:
            return "—"
        return format_html(
            '<span style="font-weight:600;color:#0d9488">{}</span>',
            d.strftime("%d/%m/%Y"),
        )

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colors = {
            "TRIAL":     "#3b82f6",
            "ACTIVA":    "#10b981",
            "MOROSA":    "#f59e0b",
            "BLOQUEADA": "#ef4444",
            "CANCELADA": "#6b7280",
        }
        c = colors.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;border-radius:4px;'
            'font-size:11px;font-weight:600;white-space:nowrap">{}</span>',
            c, obj.get_estado_display(),
        )


# ============================================================================
# PlatformInvoice
# ============================================================================

@admin.register(PlatformInvoice)
class PlatformInvoiceAdmin(ModelAdmin):
    list_display = (
        "tenant_link",
        "periodo",
        "monto",
        "estado_badge",
        "fecha_vencimiento",
        "fecha_pago",
        "dias_vencida_badge",
    )
    list_filter = ("estado", "anio", "mes")
    search_fields = ("tenant__nombre", "referencia")
    autocomplete_fields = ("tenant",)
    readonly_fields = ("creado_at", "actualizado_at")
    list_per_page = 50
    date_hierarchy = "fecha_emision"
    actions = ("marcar_pagada", "marcar_pendiente")

    @admin.display(description="Jardín", ordering="tenant__nombre")
    def tenant_link(self, obj):
        url = reverse("admin:tenants_tenant_change", args=[obj.tenant_id])
        return format_html('<a href="{}">{}</a>', url, obj.tenant.nombre)

    @admin.display(description="Periodo", ordering="-anio")
    def periodo(self, obj):
        return f"{obj.mes:02d}/{obj.anio}"

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colors = {
            "PAGADA":    "#10b981",
            "PENDIENTE": "#f59e0b",
            "VENCIDA":   "#ef4444",
            "CONDONADA": "#6b7280",
        }
        c = colors.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;border-radius:4px;'
            'font-size:11px;font-weight:600;white-space:nowrap">{}</span>',
            c, obj.get_estado_display(),
        )

    @admin.display(description="Días vencida")
    def dias_vencida_badge(self, obj):
        d = obj.dias_vencida
        if d == 0:
            return "—"
        color = "#ef4444" if d > 7 else "#f59e0b"
        return format_html(
            '<span style="color:{};font-weight:600">{} días</span>', color, d,
        )

    @admin.action(description="Marcar como PAGADA (con fecha de hoy)")
    def marcar_pagada(self, request, queryset):
        count = queryset.update(
            estado=PlatformInvoice.Estado.PAGADA, fecha_pago=date.today()
        )
        self.message_user(request, f"{count} cobro(s) marcado(s) como pagado.", messages.SUCCESS)

    @admin.action(description="Volver a PENDIENTE")
    def marcar_pendiente(self, request, queryset):
        count = queryset.update(estado=PlatformInvoice.Estado.PENDIENTE, fecha_pago=None)
        self.message_user(request, f"{count} cobro(s) vuelto(s) a pendiente.", messages.WARNING)


# ============================================================================
# PlatformCost
# ============================================================================

@admin.register(PlatformCost)
class PlatformCostAdmin(ModelAdmin):
    list_display = ("concepto", "categoria_badge", "monto", "fecha", "recurrente", "tenant")
    list_filter = ("categoria", "recurrente", "fecha")
    search_fields = ("concepto", "notas")
    autocomplete_fields = ("tenant",)
    date_hierarchy = "fecha"
    list_per_page = 30

    @admin.display(description="Categoría", ordering="categoria")
    def categoria_badge(self, obj):
        colors = {
            "HOSTING_BACK":  "#0ea5e9",
            "HOSTING_FRONT": "#8b5cf6",
            "DOMINIO":       "#f59e0b",
            "EMAIL":         "#10b981",
            "STORAGE":       "#64748b",
            "OTROS":         "#6b7280",
        }
        c = colors.get(obj.categoria, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;border-radius:4px;'
            'font-size:11px;white-space:nowrap">{}</span>',
            c, obj.get_categoria_display(),
        )
