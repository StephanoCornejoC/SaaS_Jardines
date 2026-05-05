from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cashflow.models import CashCategory, CashTransaction
from apps.students.models import Student
from shared.validators import validate_month_param, validate_year_param

from .models import MonthlyFee, Payment
from .serializers import (
    MonthlyFeeSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentRegisterSerializer,
)
from .services import generate_yape_qr


MES_INICIO_ESCOLAR = 3   # Marzo
MES_FIN_ESCOLAR = 12     # Diciembre


def _ensure_yearly_payments(student, monthly_fee, anio):
    """
    Crea los Payment (PENDIENTE) de marzo a diciembre del año si no existen.
    Enero y febrero son vacaciones — no se cobra pensión.
    """
    existentes = {
        p.mes: p
        for p in Payment.objects.filter(student=student, anio=anio)
    }
    creados = []
    for mes in range(MES_INICIO_ESCOLAR, MES_FIN_ESCOLAR + 1):
        if mes in existentes:
            continue
        ultimo_dia = monthrange(anio, mes)[1]
        dia_venc = min(monthly_fee.dia_vencimiento, ultimo_dia)
        creados.append(
            Payment(
                student=student,
                monthly_fee=monthly_fee,
                mes=mes,
                anio=anio,
                monto=monthly_fee.monto_mensual,
                estado=Payment.Estado.PENDIENTE,
                fecha_vencimiento=date(anio, mes, dia_venc),
            )
        )
    if creados:
        Payment.objects.bulk_create(creados)


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

    @action(detail=True, methods=["patch"], url_path="registrar-pago")
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

    @action(detail=True, methods=["get", "post"], url_path="generar-qr")
    def generar_qr(self, request, pk=None):
        """Genera un codigo QR para el pago (PNG image)."""
        from django.http import HttpResponse

        payment = self.get_object()
        qr_bytes = generate_yape_qr(payment.student, payment)
        response = HttpResponse(qr_bytes, content_type="image/png")
        response["Cache-Control"] = "no-cache"
        return response

    @action(detail=False, methods=["get"], url_path="por-alumno")
    def por_alumno(self, request):
        """
        Devuelve las 12 pensiones del año para un alumno. Si faltan meses,
        los crea como PENDIENTE usando la MonthlyFee del año.
        Query params: student (id), anio (default current year)
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response(
                {"error": "Parámetro 'student' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year

        student = get_object_or_404(Student, pk=student_id)
        monthly_fee = MonthlyFee.objects.filter(student=student, anio_escolar=anio).first()
        if not monthly_fee:
            return Response(
                {
                    "error": (
                        "Este alumno aún no tiene pensión configurada para el año "
                        f"{anio}. Debe registrar su matrícula primero."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _ensure_yearly_payments(student, monthly_fee, anio)

        pagos = Payment.objects.filter(
            student=student,
            anio=anio,
            mes__gte=MES_INICIO_ESCOLAR,
            mes__lte=MES_FIN_ESCOLAR,
        ).order_by("mes")
        total_pagado = pagos.filter(estado=Payment.Estado.PAGADO).aggregate(
            t=Sum("monto")
        )["t"] or Decimal("0.00")
        pendientes = pagos.exclude(
            estado__in=[Payment.Estado.PAGADO, Payment.Estado.EXONERADO]
        ).count()

        serializer = PaymentDetailSerializer(pagos, many=True)
        return Response(
            {
                "student": {
                    "id": student.id,
                    "dni": student.dni,
                    "nombre": str(student),
                    "classroom": student.classroom.nombre if student.classroom else None,
                    "edad": student.edad,
                },
                "anio_escolar": anio,
                "monto_mensual": str(monthly_fee.monto_mensual),
                "total_pagado": str(total_pagado),
                "pendientes": pendientes,
                "pagos": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], url_path="morosidad")
    def morosidad(self, request):
        """Reporte de pagos vencidos (morosidad). Solo meses lectivos (mar-dic)."""
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year
        mes = validate_month_param(request.query_params.get("mes"))

        queryset = Payment.objects.select_related("student").filter(
            anio=anio,
            estado__in=[Payment.Estado.PENDIENTE, Payment.Estado.VENCIDO],
            fecha_vencimiento__lt=date.today(),
            mes__gte=MES_INICIO_ESCOLAR,
            mes__lte=MES_FIN_ESCOLAR,
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
