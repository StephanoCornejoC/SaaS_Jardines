import time
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
# Cache "stale" persiste mucho más para servir lecturas mientras un worker
# recalcula. Anti-dogpile: si el cache primario expira y hay 10 requests
# concurrentes, solo 1 calcula y los demás reciben la versión stale en lugar
# de ejecutar el cálculo en paralelo.
DASHBOARD_STALE_TTL = 60 * 30
DASHBOARD_LOCK_TTL = 30  # Tiempo máximo razonable que puede tardar el cálculo


def _compute_resumen():
    """Hace el cálculo pesado del resumen. Aislado para testabilidad."""
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
    return data


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para el dashboard. No expone CRUD, solo acciones personalizadas.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """
        Retorna las métricas del día. Cacheado 5 min por tenant con
        protección anti-dogpile: si el cache primario expira y varios
        requests llegan simultáneamente, solo uno recalcula y el resto
        recibe la versión stale.
        """
        schema = getattr(connection, "schema_name", "public")
        today_iso = date.today().isoformat()
        cache_key = f"dashboard:resumen:{schema}:{today_iso}"
        stale_key = f"dashboard:stale:{schema}:{today_iso}"
        lock_key = f"dashboard:lock:{schema}:{today_iso}"

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # Intentamos adquirir el lock atómicamente. cache.add() es atómico
        # en DatabaseCache y RedisCache.
        got_lock = cache.add(lock_key, "1", DASHBOARD_LOCK_TTL)
        if not got_lock:
            # Otro worker está calculando. Devolvemos la versión stale si
            # existe; en su defecto, esperamos brevemente al cálculo en curso.
            stale = cache.get(stale_key)
            if stale:
                return Response(stale)
            for _ in range(10):  # hasta ~3s
                time.sleep(0.3)
                cached = cache.get(cache_key)
                if cached:
                    return Response(cached)
            # Como último recurso, calculamos sin lock para no quedarnos
            # sin respuesta. Es un caso degenerado (lock huérfano).

        try:
            data = _compute_resumen()
            cache.set(cache_key, data, DASHBOARD_CACHE_TTL)
            cache.set(stale_key, data, DASHBOARD_STALE_TTL)
            return Response(data)
        finally:
            cache.delete(lock_key)

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
