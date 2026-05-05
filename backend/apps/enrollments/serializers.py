from datetime import date

from rest_framework import serializers

from apps.cashflow.models import CashCategory, CashTransaction
from apps.payments.models import MonthlyFee

from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    classroom_nombre = serializers.CharField(
        source="classroom.nombre", read_only=True, default=None
    )
    monto_mensual = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True, required=False
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
            "monto_mensual",
            "fecha_matricula",
            "observaciones",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "fecha_matricula", "created_by", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context.get("request")
        monto_mensual = validated_data.pop("monto_mensual", None)

        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user

        enrollment = super().create(validated_data)

        student = enrollment.student
        # Asignar el aula al alumno SOLO si:
        #   - es la primera vez (no tiene aula) y
        #   - la matrícula corresponde al año actual.
        # En cualquier otro caso (matrícula del año siguiente, o cambio de aula
        # del año actual) el aula del alumno NO se toca: solo cambia con la
        # migración anual.
        if (
            student.classroom_id is None
            and enrollment.classroom_id is not None
            and enrollment.anio_escolar == date.today().year
        ):
            student.classroom = enrollment.classroom
            student.save(update_fields=["classroom"])

        if monto_mensual is not None:
            MonthlyFee.objects.update_or_create(
                student=student,
                anio_escolar=enrollment.anio_escolar,
                defaults={"monto_mensual": monto_mensual},
            )

        if enrollment.costo_matricula and enrollment.costo_matricula > 0:
            categoria, _ = CashCategory.objects.get_or_create(
                nombre="Matrículas",
                tipo=CashCategory.Tipo.INGRESO,
                defaults={"es_sistema": True},
            )
            CashTransaction.objects.create(
                categoria=categoria,
                descripcion=f"Matrícula {student} - {enrollment.anio_escolar}",
                monto=enrollment.costo_matricula,
                tipo=CashTransaction.Tipo.INGRESO,
                fecha=date.today(),
                creado_por=request.user if request and request.user.is_authenticated else None,
            )

        return enrollment

    def update(self, instance, validated_data):
        # update no debe tocar student.classroom (ver nota en create)
        validated_data.pop("monto_mensual", None)
        return super().update(instance, validated_data)
