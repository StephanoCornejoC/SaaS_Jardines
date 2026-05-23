from rest_framework import serializers

from apps.students.serializers import StudentListSerializer

from .models import Classroom


def _validate_profesores(profesor_titular, profesor_auxiliar):
    """Reglas de negocio compartidas entre serializers de Classroom.

    Espeja Classroom.clean() pero como dict de errores DRF-friendly. La doble
    validación es deliberada: DRF no llama a Model.full_clean() en .save().
    """
    errors = {}
    if profesor_titular is not None and profesor_titular.tipo != "TITULAR":
        errors["profesor_titular"] = (
            "El profesor titular debe ser de tipo TITULAR."
        )
    if profesor_auxiliar is not None and profesor_auxiliar.tipo != "AUXILIAR":
        errors["profesor_auxiliar"] = (
            "El profesor auxiliar debe ser de tipo AUXILIAR."
        )
    if (
        profesor_titular is not None
        and profesor_auxiliar is not None
        and profesor_titular.pk == profesor_auxiliar.pk
    ):
        errors["profesor_auxiliar"] = (
            "El titular y el auxiliar no pueden ser la misma persona."
        )
    return errors


class ClassroomListSerializer(serializers.ModelSerializer):
    alumnos_count = serializers.IntegerField(read_only=True)
    profesor_titular_nombre = serializers.StringRelatedField(
        source="profesor_titular", read_only=True
    )
    profesor_auxiliar_nombre = serializers.StringRelatedField(
        source="profesor_auxiliar", read_only=True
    )

    class Meta:
        model = Classroom
        fields = (
            "id",
            "nombre",
            "nivel_edad",
            "capacidad",
            "alumnos_count",
            "profesor_titular",
            "profesor_titular_nombre",
            "profesor_auxiliar",
            "profesor_auxiliar_nombre",
        )


class ClassroomDetailSerializer(serializers.ModelSerializer):
    alumnos_count = serializers.IntegerField(read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    students = StudentListSerializer(many=True, read_only=True)
    profesor_titular_nombre = serializers.StringRelatedField(
        source="profesor_titular", read_only=True
    )
    profesor_auxiliar_nombre = serializers.StringRelatedField(
        source="profesor_auxiliar", read_only=True
    )

    class Meta:
        model = Classroom
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            # Profesor titular es obligatorio al crear/editar desde la API.
            # El modelo lo mantiene null=True por compatibilidad con aulas
            # legacy creadas antes de esta regla.
            "profesor_titular": {"required": True, "allow_null": False},
        }

    def validate(self, attrs):
        # Para PATCH (partial=True) los campos faltantes en attrs deben caer
        # al valor actual de la instancia.
        instance = getattr(self, "instance", None)
        profesor_titular = attrs.get(
            "profesor_titular",
            getattr(instance, "profesor_titular", None),
        )
        profesor_auxiliar = attrs.get(
            "profesor_auxiliar",
            getattr(instance, "profesor_auxiliar", None),
        )
        errors = _validate_profesores(profesor_titular, profesor_auxiliar)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
