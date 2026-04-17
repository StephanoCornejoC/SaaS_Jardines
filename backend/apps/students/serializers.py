from rest_framework import serializers

from .models import Guardian, MedicalRecord, Student


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = "__all__"
        read_only_fields = ("id", "student")


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        exclude = ("student",)
        read_only_fields = ("id",)


class StudentListSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)
    classroom_nombre = serializers.CharField(source="classroom.nombre", read_only=True, default=None)

    class Meta:
        model = Student
        fields = ("id", "dni", "nombres", "apellidos", "edad", "classroom_nombre", "estado")


class StudentDetailSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)
    apoderados = GuardianSerializer(many=True, read_only=True)
    ficha_medica = MedicalRecordSerializer(read_only=True)

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
