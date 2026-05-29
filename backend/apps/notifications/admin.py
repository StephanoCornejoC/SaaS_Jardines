"""Admin de la app notifications.

Diseño:
  Log read-only de todos los emails que el sistema envió (o intentó
  enviar). Útil para auditoría — la directora puede confirmar que un
  email salió y a quién, y soporte interno puede diagnosticar fallas de SMTP.

  Decisiones:
  - Badge de tipo (Recordatorio / Comunicación / Alerta asistencia / Bienvenida).
  - Status visual: ✓ verde si enviado, ✗ rojo si error.
  - Preview del contenido y del error si lo hay.
  - Destinatario clickeable como mailto:.
  - Strict read-only: no se crean ni se borran desde el admin. Son
    artefactos generados por jobs y signals.
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html

from .models import EmailLog


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = (
        "created_at_display",
        "tipo_badge",
        "destinatario_link",
        "asunto",
        "status_badge",
        "error_short",
    )
    list_display_links = ("asunto",)
    list_filter = ()
    search_fields = ("destinatario", "asunto", "contenido", "error")
    readonly_fields = (
        "destinatario", "asunto", "contenido", "tipo",
        "enviado", "error", "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        ("Email", {
            "fields": (("destinatario", "tipo"), "asunto", "contenido"),
        }),
        ("Estado de envío", {"fields": (("enviado", "created_at"), "error")}),
    )

    def has_add_permission(self, request):
        # Los EmailLog son generados por jobs y signals. NO se crean
        # manualmente desde el admin.
        return False

    def has_change_permission(self, request, obj=None):
        # Read-only: son registros históricos, modificarlos rompe trazabilidad.
        return False

    def has_delete_permission(self, request, obj=None):
        # Stephano (superadmin) puede limpiar logs viejos si es necesario.
        return super().has_delete_permission(request, obj)

    # ---- columnas ----

    @admin.display(description="Fecha", ordering="-created_at")
    def created_at_display(self, obj):
        return format_html(
            '<span>{}</span><br>'
            '<span style="color:#94a3b8;font-size:11px">{}</span>',
            obj.created_at.strftime("%d/%m/%Y"),
            obj.created_at.strftime("%H:%M"),
        )

    @admin.display(description="Tipo", ordering="tipo")
    def tipo_badge(self, obj):
        colors = {
            "RECORDATORIO_PAGO":  "#f59e0b",
            "COMUNICACION":       "#0d9488",
            "ALERTA_ASISTENCIA":  "#ef4444",
            "BIENVENIDA":         "#3b82f6",
        }
        return _badge(obj.get_tipo_display(),
                      colors.get(obj.tipo, "#6b7280"))

    @admin.display(description="Destinatario", ordering="destinatario")
    def destinatario_link(self, obj):
        if not obj.destinatario:
            return format_html('<span style="color:#94a3b8">—</span>')
        return format_html(
            '<a href="mailto:{}" style="color:#0d9488">{}</a>',
            obj.destinatario, obj.destinatario,
        )

    @admin.display(description="Estado", ordering="enviado")
    def status_badge(self, obj):
        if obj.enviado:
            return format_html(
                '<span style="color:#10b981;font-weight:700">✓ Enviado</span>'
            )
        if obj.error:
            return format_html(
                '<span style="color:#ef4444;font-weight:700">✗ Error</span>'
            )
        return _badge("Pendiente", "#f59e0b")

    @admin.display(description="Detalle del error")
    def error_short(self, obj):
        if not obj.error:
            return format_html('<span style="color:#94a3b8">—</span>')
        texto = obj.error.strip()
        if len(texto) > 60:
            texto = texto[:60] + "…"
        return format_html(
            '<span style="color:#ef4444" title="{}">{}</span>',
            obj.error, texto,
        )
