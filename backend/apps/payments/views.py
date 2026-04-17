from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cashflow.models import CashCategory, CashTransaction
from apps.users.permissions import IsAdminJardinOrAbove
from shared.validators import validate_month_param, validate_year_param

from .models import MonthlyFee, Payment
from .serializers import (
    MonthlyFeeSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentRegisterSerializer,
)
from .services import generate_yape_qr


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Payment.objects.select_related("student", "monthly_fee")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["mes", "anio", "estado", "student"]
    search_fields = ["student__nombres", "student__apellidos", "student__dni"]
    ordering_fields = ["anio", "mes", "fecha_vencimiento", "student__apellidos"]
    ordering = ["-anio", "-mes"]

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        if self.action == "registrar_pago":
            return PaymentRegisterSerializer
        return PaymentDetailSerializer

    @action(detail=True, methods=["patch"], url_path="registrar-pago", permission_classes=[IsAdminJardinOrAbove])
    def registrar_pago(self, request, pk=None):
        """Registrar el pago de una pension."""
        payment = self.get_object()
        serializer = PaymentRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.estado = serializer.validated_data["estado"]
        payment.metodo_pago = serializer.validated_data.get("metodo_pago", "")
        payment.comprobante = serializer.validated_data.get("comprobante", "")
        payment.observaciones = serializer.validated_data.get("observaciones", "")

        if payment.estado == Payment.Estado.PAGADO:
            payment.fecha_pago = date.today()

        if request.user.is_authenticated:
            payment.registrado_por = request.user

        payment.save()

        if payment.estado == Payment.Estado.PAGADO:
            category, _ = CashCategory.objects.get_or_create(
                nombre="Pensiones",
                tipo="INGRESO",
                defaults={"es_sistema": True},
            )
            CashTransaction.objects.create(
                categoria=category,
                descripcion=f"Pension {payment.student} - {payment.mes}/{payment.anio}",
                monto=payment.monto,
                tipo="INGRESO",
                fecha=payment.fecha_pago or date.today(),
                referencia_pago=payment,
                creado_por=request.user,
            )

        return Response(PaymentDetailSerializer(payment).data)

    @action(detail=True, methods=["post"], url_path="generar-qr")
    def generar_qr(self, request, pk=None):
        """Genera un codigo QR para el pago."""
        payment = self.get_object()
        qr_url = generate_yape_qr(payment.student, payment)
        return Response({"qr_url": qr_url}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="morosidad")
    def morosidad(self, request):
        """Reporte de pagos vencidos (morosidad)."""
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year
        mes = validate_month_param(request.query_params.get("mes"))

        queryset = Payment.objects.select_related("student").filter(
            anio=anio,
            estado__in=[Payment.Estado.PENDIENTE, Payment.Estado.VENCIDO],
            fecha_vencimiento__lt=date.today(),
        )

        if mes:
            queryset = queryset.filter(mes=mes)

        serializer = PaymentListSerializer(queryset, many=True)
        return Response(
            {
                "total_morosos": queryset.count(),
                "monto_total_pendiente": queryset.aggregate(total=Sum("monto"))["total"] or Decimal("0.00"),
                "detalle": serializer.data,
            }
        )


class MonthlyFeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = MonthlyFee.objects.select_related("student")
    serializer_class = MonthlyFeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["anio_escolar", "student"]
    search_fields = ["student__nombres", "student__apellidos", "student__dni"]
    ordering = ["-anio_escolar", "student__apellidos"]
