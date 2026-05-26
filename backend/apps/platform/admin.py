from datetime import date
from decimal import Decimal

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Plan, PlatformCost, PlatformInvoice, TenantSubscription


@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    list_display = ("nombre", "precio_mensual", "activo", "creado_at")
    list_filter = ()
    list_editable = ("precio_mensual", "activo")
    search_fields = ("nombre",)
    readonly_fields = ("creado_at", "actualizado_at")

    def has_add_permission(self, request):
        # Solo permitir 1 plan activo. Si ya hay uno, no se crea otro.
        if Plan.objects.filter(activo=True).exists():
            return False
        return super().has_add_permission(request)


@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(ModelAdmin):
    list_display = (
        "tenant_link",
        "plan_link",       # ← callable wrapper para que list_display_links lo use
        "precio_acordado",
        "fecha_alta",
        "trial_hasta",
        "estado_badge",
    )
    # Indicarle a Django CUAL columna del listado debe ser el link al
    # change_view. Sin esto, el primer campo (tenant_link) ya tiene su
    # propio <a> al tenant_change y Django no genera link al subscription
    # change → el SUPERADMIN no podia editar estado/precio/fechas.
    list_display_links = ("plan_link",)
    list_filter = ()
    search_fields = ("tenant__nombre", "tenant__ruc")
    autocomplete_fields = ("tenant", "plan")
    readonly_fields = ("creado_at", "actualizado_at")
    list_per_page = 30

    fieldsets = (
        ("Jardín", {"fields": ("tenant", "plan", "precio_acordado")}),
        ("Periodo", {"fields": ("fecha_alta", "trial_hasta", "estado")}),
        ("Notas", {"fields": ("notas",)}),
        ("Auditoría", {"classes": ("collapse",), "fields": ("creado_at", "actualizado_at")}),
    )

    @admin.display(description="Jardín", ordering="tenant__nombre")
    def tenant_link(self, obj):
        url = reverse("admin:tenants_tenant_change", args=[obj.tenant_id])
        return format_html('<a href="{}">{}</a>', url, obj.tenant.nombre)

    @admin.display(description="Plan", ordering="plan__nombre")
    def plan_link(self, obj):
        """
        Wrapper sobre el campo plan que se renderiza como texto plano
        (sin <a>). Django (gracias a list_display_links) lo envuelve
        automaticamente en un link al change_view de esta Subscription.
        Asi el SUPERADMIN puede editar precio_acordado, estado, fechas, etc.
        """
        return obj.plan.nombre if obj.plan else "(sin plan)"

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colors = {
            "TRIAL": "#3b82f6",
            "ACTIVA": "#10b981",
            "MOROSA": "#f59e0b",
            "BLOQUEADA": "#ef4444",
            "CANCELADA": "#6b7280",
        }
        c = colors.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            c, obj.get_estado_display(),
        )


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
    list_filter = ()
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
            "PAGADA": "#10b981",
            "PENDIENTE": "#f59e0b",
            "VENCIDA": "#ef4444",
            "CONDONADA": "#6b7280",
        }
        c = colors.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">{}</span>',
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


@admin.register(PlatformCost)
class PlatformCostAdmin(ModelAdmin):
    list_display = (
        "concepto", "categoria_badge", "monto", "fecha", "recurrente",
        "destino_display",
    )
    list_filter = ()
    search_fields = ("concepto", "notas")
    autocomplete_fields = ("tenant",)
    date_hierarchy = "fecha"
    list_per_page = 30

    fieldsets = (
        ("Concepto", {"fields": ("concepto", "categoria", "monto", "fecha", "recurrente")}),
        ("Destino del costo", {
            "fields": ("tenant",),
            "description": (
                "Si el costo aplica a un jardín específico, asignar Tenant. "
                "Si es un costo genérico del SaaS (Railway, dominio, email), "
                "dejarlo vacío."
            ),
        }),
        ("Notas", {"fields": ("notas",)}),
    )

    @admin.display(description="Aplica a")
    def destino_display(self, obj):
        if obj.tenant_id:
            return format_html(
                '<span style="color:#0d9488;font-weight:600">Jardín · {}</span>',
                obj.tenant.nombre,
            )
        return format_html(
            '<span style="color:#64748b">SaaS (genérico)</span>'
        )

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
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            c, obj.get_categoria_display(),
        )
