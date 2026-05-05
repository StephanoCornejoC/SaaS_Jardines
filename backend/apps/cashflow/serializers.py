from rest_framework import serializers

from .models import CashCategory, CashTransaction, MonthlyClosure


class CashCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CashCategory
        fields = ("id", "nombre", "tipo", "es_sistema", "activo", "created_at")
        read_only_fields = ("id", "created_at")


class CashTransactionSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source="categoria.nombre", read_only=True
    )
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CashTransaction
        fields = (
            "id",
            "categoria",
            "categoria_nombre",
            "descripcion",
            "monto",
            "tipo",
            "fecha",
            "referencia_pago",
            "referencia_teacher_payment",
            "creado_por",
            "creado_por_nombre",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "creado_por", "created_at", "updated_at")

    def get_creado_por_nombre(self, obj):
        if not obj.creado_por:
            return None
        u = obj.creado_por
        full = (u.get_full_name() or "").strip()
        return full or u.email

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["creado_por"] = request.user
        return super().create(validated_data)


class MonthlyClosureSerializer(serializers.ModelSerializer):
    cerrado_por_nombre = serializers.StringRelatedField(
        source="cerrado_por", read_only=True
    )

    class Meta:
        model = MonthlyClosure
        fields = (
            "id",
            "mes",
            "anio",
            "total_ingresos",
            "total_egresos",
            "balance",
            "cerrado_por",
            "cerrado_por_nombre",
            "observaciones",
            "fecha_cierre",
        )
        read_only_fields = (
            "id",
            "total_ingresos",
            "total_egresos",
            "balance",
            "fecha_cierre",
        )


class CashflowSummarySerializer(serializers.Serializer):
    mes = serializers.IntegerField()
    anio = serializers.IntegerField()
    total_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_egresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    cerrado = serializers.BooleanField()
