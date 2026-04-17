from datetime import date, timedelta

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DashboardMetric
from .serializers import DashboardMetricSerializer, DashboardSummarySerializer
from .services import calculate_daily_metrics


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para el dashboard. No expone CRUD, solo acciones personalizadas.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Retorna las métricas más recientes."""
        metric = DashboardMetric.objects.first()

        if not metric:
            # Si no hay métricas, intentar calcular
            metric = calculate_daily_metrics()

        serializer = DashboardSummarySerializer(metric)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="historico")
    def historico(self, request):
        """Retorna las métricas de los últimos 30 días para gráficos."""
        try:
            dias = int(request.query_params.get("dias", 30))
        except (ValueError, TypeError):
            dias = 30
        dias = min(dias, 90)  # máximo 90 días

        fecha_desde = date.today() - timedelta(days=dias)

        metrics = DashboardMetric.objects.filter(
            fecha__gte=fecha_desde
        ).order_by("fecha")

        serializer = DashboardMetricSerializer(metrics, many=True)
        return Response(serializer.data)
