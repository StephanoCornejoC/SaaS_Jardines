from rest_framework import serializers

from apps.students.serializers import StudentListSerializer

from .models import Classroom


class ClassroomListSerializer(serializers.ModelSerializer):
    alumnos_count = serializers.IntegerField(read_only=True)
    profesor_titular_nombre = serializers.StringRelatedField(
        source="profesor_titular", read_only=True
    )

    class Meta:
        model = Classroom
        fields = (
            "id",
            "nombre",
            "nivel_edad",
            "capacidad",
            "alumnos_count",
            "profesor_titular_nombre",
            "activo",
        )


class ClassroomDetailSerializer(serializers.ModelSerializer):
    alumnos_count = serializers.IntegerField(read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    students = StudentListSerializer(many=True, read_only=True)

    class Meta:
        model = Classroom
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
