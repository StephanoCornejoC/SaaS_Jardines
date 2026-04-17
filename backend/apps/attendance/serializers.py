from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    classroom_nombre = serializers.StringRelatedField(
        source="classroom", read_only=True
    )

    class Meta:
        model = Attendance
        fields = (
            "id",
            "student",
            "student_nombre",
            "classroom",
            "classroom_nombre",
            "fecha",
            "estado",
            "observaciones",
            "registrado_por",
            "created_at",
        )
        read_only_fields = ("id", "registrado_por", "created_at")


class BulkAttendanceItemSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=Attendance.Estado.choices)
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")


class BulkAttendanceSerializer(serializers.Serializer):
    classroom_id = serializers.IntegerField()
    fecha = serializers.DateField()
    asistencias = BulkAttendanceItemSerializer(many=True)


class AttendanceReportSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_nombre = serializers.CharField()
    total_presentes = serializers.IntegerField()
    total_ausentes = serializers.IntegerField()
    total_tardanzas = serializers.IntegerField()
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2)
