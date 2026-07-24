from rest_framework import serializers

from .models import Consent, ConsentDocument


class ConsentDocumentSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ConsentDocument
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "version",
            "titulo",
            "contenido",
            "obligatorio",
            "vigente_desde",
            "activo",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ConsentSerializer(serializers.ModelSerializer):
    """Lectura: muestra el registro de consentimiento con datos legibles."""

    documento_display = serializers.CharField(source="documento.__str__", read_only=True)
    student_nombre = serializers.CharField(source="student.__str__", read_only=True)
    guardian_nombre = serializers.CharField(source="guardian.__str__", read_only=True, default=None)
    registrado_por_email = serializers.CharField(
        source="registrado_por.email", read_only=True, default=None
    )

    class Meta:
        model = Consent
        fields = (
            "id",
            "documento",
            "documento_display",
            "student",
            "student_nombre",
            "guardian",
            "guardian_nombre",
            "otorgado",
            "fecha",
            "ip",
            "user_agent",
            "registrado_por",
            "registrado_por_email",
            "notas",
            "created_at",
        )
        # ip / user_agent / registrado_por se capturan del request, no del
        # cliente. fecha por defecto = ahora (se puede sobreescribir si el
        # consentimiento se firmó en papel en otra fecha).
        read_only_fields = ("id", "ip", "user_agent", "registrado_por", "created_at")

    def validate(self, data):
        documento = data.get("documento")
        if documento is not None and not documento.activo:
            raise serializers.ValidationError(
                {"documento": "No se puede registrar un consentimiento sobre un documento inactivo."}
            )
        return data
