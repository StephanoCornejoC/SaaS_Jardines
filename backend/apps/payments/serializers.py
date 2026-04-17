from rest_framework import serializers

from .models import MonthlyFee, Payment


class MonthlyFeeSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )

    class Meta:
        model = MonthlyFee
        fields = (
            "id",
            "student",
            "student_nombre",
            "anio_escolar",
            "monto_mensual",
            "dia_vencimiento",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class PaymentListSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "student_nombre",
            "mes",
            "anio",
            "monto",
            "estado",
            "fecha_vencimiento",
            "is_overdue",
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    student_nombre = serializers.StringRelatedField(
        source="student", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class PaymentRegisterSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Payment.Estado.choices)
    metodo_pago = serializers.ChoiceField(
        choices=Payment.MetodoPago.choices, required=False, allow_blank=True
    )
    comprobante = serializers.CharField(required=False, allow_blank=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)
