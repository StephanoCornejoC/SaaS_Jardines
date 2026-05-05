from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cashflow.models import CashTransaction

from .models import DashboardMetric
from .serializers import DashboardMetricSerializer, DashboardSummarySerializer
from .services import calculate_daily_metrics


# Cache de 5 minutos para el resumen del dashboard. Cada tenant tiene su
# propia entrada (clave incluye schema_name) — recalcular en cada GET es muy
# costoso (8 queries pesadas + escritura). 5 minutos es aceptable porque
# los KPIs no cambian al segundo.
DASHBOARD_CACHE_TTL = 60 * 5


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para el dashboard. No expone CRUD, solo acciones personalizadas.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Retorna las métricas del día. Cacheado 5 min por tenant."""
        schema = getattr(connection, "schema_name", "public")
        cache_key = f"dashboard:resumen:{schema}:{date.today().isoformat()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        metric = calculate_daily_metrics()
        data = dict(DashboardSummarySerializer(metric).data)

        anio = date.today().year
        ingresos_mes_qs = (
            CashTransaction.objects.filter(
                tipo=CashTransaction.Tipo.INGRESO,
                fecha__year=anio,
            )
            .values("fecha__month")
            .annotate(total=Sum("monto"))
            .order_by("fecha__month")
        )
        por_mes = {row["fecha__month"]: row["total"] for row in ingresos_mes_qs}
        data["ingresos_por_mes"] = [
            {"mes": m, "total": str(por_mes.get(m, Decimal("0.00")))}
            for m in range(1, 13)
        ]

        cache.set(cache_key, data, DASHBOARD_CACHE_TTL)
        return Response(data)

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
