from rest_framework import serializers

from .models import DashboardMetric


class DashboardMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardMetric
        fields = (
            "id",
            "fecha",
            "total_alumnos",
            "total_profesores",
            "alumnos_por_nivel",
            "ingresos_mes",
            "egresos_mes",
            "balance_mes",
            "porcentaje_morosidad",
            "porcentaje_asistencia",
            "created_at",
        )
        read_only_fields = fields


class DashboardSummarySerializer(serializers.Serializer):
    fecha = serializers.DateField()
    total_alumnos = serializers.IntegerField()
    total_profesores = serializers.IntegerField()
    alumnos_por_nivel = serializers.JSONField()
    ingresos_mes = serializers.DecimalField(max_digits=12, decimal_places=2)
    egresos_mes = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_mes = serializers.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_morosidad = serializers.DecimalField(max_digits=5, decimal_places=2)
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2)
