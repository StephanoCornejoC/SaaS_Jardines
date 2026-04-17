from rest_framework import serializers

from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    classroom_nombre = serializers.CharField(
        source="classroom.nombre", read_only=True, default=None
    )

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student",
            "student_nombre",
            "classroom",
            "classroom_nombre",
            "anio_escolar",
            "costo_matricula",
            "estado",
            "fecha_matricula",
            "observaciones",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "fecha_matricula", "created_by", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)
