from rest_framework import serializers

from .models import Teacher, TeacherContract, TeacherPayment


class TeacherPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherPayment
        fields = "__all__"
        read_only_fields = ("id", "contract", "created_at")


class TeacherContractSerializer(serializers.ModelSerializer):
    payments = TeacherPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = TeacherContract
        fields = "__all__"
        read_only_fields = ("id", "teacher", "created_at")


class TeacherListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ("id", "dni", "nombre_completo", "especialidad", "activo")

    def get_nombre_completo(self, obj):
        return f"{obj.apellidos}, {obj.nombres}"


class TeacherDetailSerializer(serializers.ModelSerializer):
    contracts = TeacherContractSerializer(many=True, read_only=True)

    class Meta:
        model = Teacher
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
