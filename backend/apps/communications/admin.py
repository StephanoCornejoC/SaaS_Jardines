"""Admin de la app communications.

Diseño:
  Pulido para que la directora consulte las comunicaciones enviadas y
  vea su estado (enviada/pendiente). El alta y envío se hace desde el
  frontend del jardín — el admin es para auditoría y consulta.

  Decisiones:
  - Badge de tipo (General / Por aula).
  - Badge de estado de envío (enviada verde / pendiente ámbar).
  - Preview del contenido (50 chars + tooltip).
  - Link clickeable al aula (si aplica).
  - Fecha de envío formateada en local time.
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import Communication


_BADGE = (
    'background:{bg};color:#fff;padding:2px 8px;border-radius:4px;'
    'font-size:11px;font-weight:600;letter-spacing:0.3px;text-transform:uppercase'
)


def _badge(text, bg):
    return format_html('<span style="{}">{}</span>',
                       _BADGE.format(bg=bg), text)


@admin.register(Communication)
class CommunicationAdmin(ModelAdmin):
    list_display = (
        "titulo",
        "tipo_badge",
        "destinatario_display",
        "contenido_preview",
        "envio_status",
        "enviado_por",
    )
    list_display_links = ("titulo",)
    list_filter = ()
    search_fields = (
        "titulo", "contenido", "enviado_por__email",
        "classroom__nombre",
    )
    autocomplete_fields = ("classroom",)
    readonly_fields = (
        "created_at", "updated_at", "fecha_envio", "enviado", "enviado_por",
    )
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        ("Mensaje", {"fields": ("titulo", "tipo", "classroom", "contenido")}),
        ("Estado de envío", {
            "classes": ("collapse",),
            "fields": ("enviado", "fecha_envio", "enviado_por"),
            "description": (
                "Estos campos son automáticos. Se actualizan al enviar la "
                "comunicación desde el frontend del jardín."
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("classroom", "enviado_por")
        )

    # ---- columnas ----

    @admin.display(description="Tipo", ordering="tipo")
    def tipo_badge(self, obj):
        colors = {
            "GENERAL":  "#8b5cf6",
            "POR_AULA": "#0d9488",
        }
        return _badge(obj.get_tipo_display(),
                      colors.get(obj.tipo, "#6b7280"))

    @admin.display(description="Destinatario")
    def destinatario_display(self, obj):
        if obj.tipo == "POR_AULA":
            if not obj.classroom_id:
                return format_html(
                    '<span style="color:#ef4444">⚠ sin aula asignada</span>'
                )
            url = reverse(
                "admin:classrooms_classroom_change", args=[obj.classroom_id],
            )
            return format_html(
                '<a href="{}" style="color:#0d9488;font-weight:600">{}</a>',
                url, obj.classroom.nombre,
            )
        return format_html(
            '<span style="color:#8b5cf6;font-weight:600">Todo el jardín</span>'
        )

    @admin.display(description="Contenido")
    def contenido_preview(self, obj):
        if not obj.contenido:
            return format_html('<span style="color:#94a3b8">—</span>')
        texto = obj.contenido.strip()
        if len(texto) > 50:
            texto = texto[:50] + "…"
        return format_html(
            '<span title="{}">{}</span>', obj.contenido, texto,
        )

    @admin.display(description="Estado", ordering="enviado")
    def envio_status(self, obj):
        if obj.enviado:
            fecha = obj.fecha_envio.strftime("%d/%m/%Y %H:%M") if obj.fecha_envio else "—"
            return format_html(
                '<span style="color:#10b981;font-weight:600">✓ Enviado</span>'
                '<br><span style="color:#94a3b8;font-size:11px">{}</span>',
                fecha,
            )
        return _badge("Pendiente", "#f59e0b")
