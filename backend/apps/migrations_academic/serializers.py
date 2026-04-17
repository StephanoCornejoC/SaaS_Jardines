from rest_framework import serializers

from .models import AcademicMigration, MigrationDetail


class MigrationDetailSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    aula_origen_nombre = serializers.StringRelatedField(
        source="aula_origen", read_only=True
    )
    aula_destino_nombre = serializers.StringRelatedField(
        source="aula_destino", read_only=True
    )

    class Meta:
        model = MigrationDetail
        fields = (
            "id",
            "student",
            "student_nombre",
            "aula_origen",
            "aula_origen_nombre",
            "aula_destino",
            "aula_destino_nombre",
            "estado_anterior",
            "estado_nuevo",
        )


class AcademicMigrationSerializer(serializers.ModelSerializer):
    details = MigrationDetailSerializer(many=True, read_only=True)
    ejecutado_por_nombre = serializers.StringRelatedField(
        source="ejecutado_por", read_only=True
    )

    class Meta:
        model = AcademicMigration
        fields = (
            "id",
            "anio_origen",
            "anio_destino",
            "ejecutado_por",
            "ejecutado_por_nombre",
            "fecha",
            "total_migrados",
            "status",
            "observaciones",
            "details",
        )
        read_only_fields = ("id", "fecha", "total_migrados")


class MigrationPreviewSerializer(serializers.Serializer):
    anio_origen = serializers.IntegerField()
    anio_destino = serializers.IntegerField()
    total_alumnos = serializers.IntegerField()
    por_nivel = serializers.ListField(child=serializers.DictField())
    promueven = serializers.ListField(child=serializers.DictField())
    egresan = serializers.ListField(child=serializers.DictField())
    sin_aula_destino = serializers.ListField(child=serializers.DictField())
