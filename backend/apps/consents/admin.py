from django.contrib import admin

from .models import Consent, ConsentDocument


@admin.register(ConsentDocument)
class ConsentDocumentAdmin(admin.ModelAdmin):
    list_display = ("tipo", "version", "titulo", "obligatorio", "activo", "vigente_desde")
    list_filter = ("tipo", "activo", "obligatorio")
    search_fields = ("titulo", "contenido")
    ordering = ("tipo", "-version")


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("student", "documento", "otorgado", "guardian", "fecha", "registrado_por")
    list_filter = ("otorgado", "documento__tipo")
    search_fields = ("student__nombres", "student__apellidos", "guardian__nombres", "guardian__apellidos")
    date_hierarchy = "fecha"
    # Evidencia: solo lectura desde el admin. Se agregan vía API/flujo, no a mano.
    readonly_fields = (
        "documento", "student", "guardian", "otorgado", "fecha",
        "ip", "user_agent", "registrado_por", "notas", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
