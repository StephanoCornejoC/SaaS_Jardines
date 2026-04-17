from datetime import date

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminJardinOrAbove
from shared.validators import validate_date_param, validate_month_param, validate_year_param

from .models import CashCategory, CashTransaction, MonthlyClosure
from .serializers import (
    CashCategorySerializer,
    CashflowSummarySerializer,
    CashTransactionSerializer,
    MonthlyClosureSerializer,
)
from .services import close_month, get_cashflow_summary


class CashCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CashCategory.objects.all()
    serializer_class = CashCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["tipo", "activo", "es_sistema"]
    search_fields = ["nombre"]


class CashTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CashTransaction.objects.select_related(
        "categoria", "referencia_pago", "referencia_teacher_payment"
    )
    serializer_class = CashTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "categoria"]
    search_fields = ["descripcion"]
    ordering_fields = ["fecha", "monto", "created_at"]
    ordering = ["-fecha"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro por rango de fechas
        fecha_desde = validate_date_param(
            self.request.query_params.get("fecha_desde"), "fecha_desde"
        )
        fecha_hasta = validate_date_param(
            self.request.query_params.get("fecha_hasta"), "fecha_hasta"
        )
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        # Filtro por mes y anio
        mes = validate_month_param(self.request.query_params.get("mes"))
        anio = validate_year_param(self.request.query_params.get("anio"))
        if mes:
            queryset = queryset.filter(fecha__month=mes)
        if anio:
            queryset = queryset.filter(fecha__year=anio)

        return queryset

    @action(detail=False, methods=["get"], url_path="resumen-anual")
    def resumen_anual(self, request):
        """Resumen anual del flujo de caja con desglose mensual."""
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year
        summary = get_cashflow_summary(anio)
        serializer = CashflowSummarySerializer(summary, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="cerrar-mes", permission_classes=[IsAdminJardinOrAbove])
    def cerrar_mes(self, request):
        """Cierra el mes contable generando un registro de cierre."""
        mes = request.data.get("mes")
        anio = request.data.get("anio")

        if not mes or not anio:
            return Response(
                {"error": "Se requieren los campos 'mes' y 'anio'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            closure = close_month(int(mes), int(anio), request.user)
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MonthlyClosureSerializer(closure)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MonthlyClosureViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = MonthlyClosure.objects.select_related("cerrado_por")
    serializer_class = MonthlyClosureSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["mes", "anio"]
    ordering = ["-anio", "-mes"]
