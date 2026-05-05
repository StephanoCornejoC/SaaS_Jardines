from rest_framework import serializers

from .models import Communication


class CommunicationSerializer(serializers.ModelSerializer):
    classroom_nombre = serializers.StringRelatedField(
        source="classroom", read_only=True
    )
    enviado_por_nombre = serializers.StringRelatedField(
        source="enviado_por", read_only=True
    )

    class Meta:
        model = Communication
        fields = (
            "id",
            "titulo",
            "contenido",
            "tipo",
            "classroom",
            "classroom_nombre",
            "enviado_por",
            "enviado_por_nombre",
            "fecha_envio",
            "enviado",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "enviado_por",
            "enviado_por_nombre",
            "fecha_envio",
            "enviado",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["enviado_por"] = request.user
        return super().create(validated_data)
