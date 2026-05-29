from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cashflow.models import CashCategory, CashTransaction
from apps.users.permissions import IsAdminJardinOrAbove
from shared.validators import validate_year_param

from .models import Teacher, TeacherContract, TeacherPayment
from .serializers import (
    TeacherContractSerializer,
    TeacherDetailSerializer,
    TeacherListSerializer,
    TeacherPaymentSerializer,
)


class TeacherViewSet(viewsets.ModelViewSet):
    # Solo admin: una profesora no puede modificarse a sí misma ni ver
    # contratos/sueldos de colegas.
    permission_classes = [IsAdminJardinOrAbove]
    queryset = Teacher.objects.prefetch_related("contracts__payments")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombres", "apellidos", "dni"]
    ordering_fields = ["apellidos", "nombres", "fecha_ingreso"]
    ordering = ["apellidos"]

    def get_serializer_class(self):
        if self.action == "list":
            return TeacherListSerializer
        return TeacherDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'registrar_sueldo', 'actualizar_sueldo']:
            return [IsAdminJardinOrAbove()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["patch"], url_path="actualizar-sueldo")
    def actualizar_sueldo(self, request, pk=None):
        """Actualiza el sueldo del contrato activo del profesor.

        UX para la directora: el sueldo se siente como propiedad del
        profesor. Internamente, este endpoint:
          - Si hay contrato activo → modifica `sueldo` del más reciente.
          - Si NO hay contrato activo → crea uno con sueldo + tipo +
            fecha_inicio=hoy, activo=True. Default `tipo=TIEMPO_COMPLETO`
            (la directora puede ajustar después desde el admin si hace falta).

        Body (JSON):
          sueldo (str)        -- requerido, decimal positivo
          tipo_contrato (str) -- opcional, default TIEMPO_COMPLETO
                                  (TIEMPO_COMPLETO | MEDIO_TIEMPO | POR_HORAS)

        Decisión de diseño: este endpoint MUTA el contrato existente.
        NO crea histórico (cerrar contrato anterior + abrir uno nuevo).
        Si Stephano necesita preservar historia de cambios de sueldo
        (auditoría contable), lo hace desde el admin Django creando un
        contrato nuevo con fecha_inicio futura y cerrando el anterior.
        """
        teacher = self.get_object()

        sueldo_raw = request.data.get("sueldo")
        if sueldo_raw in (None, ""):
            return Response(
                {"error": "El campo 'sueldo' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sueldo = Decimal(str(sueldo_raw))
            if sueldo <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"error": "sueldo inválido (debe ser un decimal positivo)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_contrato = request.data.get("tipo_contrato", "TIEMPO_COMPLETO")
        valid_tipos = {c.value for c in TeacherContract.TipoContrato}
        if tipo_contrato not in valid_tipos:
            return Response(
                {"error": f"tipo_contrato inválido. Opciones: {sorted(valid_tipos)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract = (
            teacher.contracts
            .filter(activo=True)
            .order_by("-fecha_inicio")
            .first()
        )

        with transaction.atomic():
            if contract is None:
                contract = TeacherContract.objects.create(
                    teacher=teacher,
                    tipo=tipo_contrato,
                    sueldo=sueldo,
                    fecha_inicio=date.today(),
                    activo=True,
                )
                created = True
            else:
                contract.sueldo = sueldo
                contract.tipo = tipo_contrato
                contract.save(update_fields=["tipo", "sueldo"])
                created = False

        return Response(
            {
                "contract_id": contract.id,
                "sueldo": str(contract.sueldo),
                "tipo": contract.tipo,
                "tipo_display": contract.get_tipo_display(),
                "created": created,
            },
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # Sueldos: vista del año + registrar pago con auto-vinculación a caja
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="sueldos")
    def sueldos(self, request, pk=None):
        """Devuelve los pagos del año del profesor con su contrato activo.

        Diferencia con `payments.por_alumno`: acá NO pre-creamos los 12
        meses (TeacherPayment no tiene estado PENDIENTE; existe solo
        cuando el pago se hizo). El frontend renderiza 12 slots y matchea
        contra `pagos` por el campo `mes`.

        Query params:
          anio (default: año actual)
        """
        teacher = self.get_object()
        anio = (
            validate_year_param(request.query_params.get("anio"))
            or date.today().year
        )

        contract = (
            teacher.contracts
            .filter(activo=True)
            .order_by("-fecha_inicio")
            .first()
        )
        if contract is None:
            return Response(
                {
                    "error": (
                        f"{teacher} no tiene un contrato activo. "
                        "Cree un contrato desde el admin antes de registrar sueldos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pagos = (
            TeacherPayment.objects
            .filter(contract=contract, anio=anio)
            .order_by("mes")
        )
        total_pagado = (
            pagos.aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        )
        meses_pagados = pagos.count()

        return Response({
            "teacher": {
                "id": teacher.id,
                "dni": teacher.dni,
                "nombre": str(teacher),
                "nombres": teacher.nombres,
                "apellidos": teacher.apellidos,
                "tipo": teacher.tipo,
            },
            "contract": {
                "id": contract.id,
                "tipo": contract.tipo,
                "tipo_display": contract.get_tipo_display(),
                "sueldo": str(contract.sueldo),
                "fecha_inicio": contract.fecha_inicio,
                "fecha_fin": contract.fecha_fin,
                "activo": contract.activo,
            },
            "anio": anio,
            "sueldo_mensual": str(contract.sueldo),
            "total_pagado": str(total_pagado),
            "meses_pagados": meses_pagados,
            "meses_pendientes": 12 - meses_pagados,
            "pagos": TeacherPaymentSerializer(pagos, many=True).data,
        })

    @action(detail=True, methods=["post"], url_path="registrar-sueldo")
    def registrar_sueldo(self, request, pk=None):
        """Registra el pago del sueldo de un mes Y crea el CashTransaction
        EGRESO vinculado en una transacción atómica.

        Body (JSON):
          contract  (int)  -- requerido, contrato al que aplica
          mes       (int)  -- requerido, 1..12
          anio      (int)  -- requerido
          monto     (str)  -- requerido, decimal con dos decimales
          fecha_pago (str) -- requerido, YYYY-MM-DD
          metodo_pago (str)-- requerido (TRANSFERENCIA | EFECTIVO | DEPOSITO)
          comprobante (str) -- opcional
          observaciones (str) -- opcional

        Reglas:
          - Solo ADMIN_JARDIN o superior (igual que mensualidades de alumnos).
          - Idempotencia: `unique_together(contract, mes, anio)` impide
            registrar dos veces el mismo mes.
          - El CashTransaction usa `referencia_teacher_payment` (FK ya
            existente) para vincularse al pago, igual que `referencia_pago`
            vincula las mensualidades de alumnos a sus ingresos.
        """
        teacher = self.get_object()

        # ---- Validación de campos ----
        required = ("contract", "mes", "anio", "monto", "fecha_pago", "metodo_pago")
        missing = [f for f in required if request.data.get(f) in (None, "")]
        if missing:
            return Response(
                {"error": f"Faltan campos requeridos: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Parsing y normalización ----
        try:
            mes = int(request.data["mes"])
            anio = int(request.data["anio"])
        except (TypeError, ValueError):
            return Response(
                {"error": "mes y anio deben ser enteros."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (1 <= mes <= 12):
            return Response(
                {"error": "mes debe estar entre 1 y 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            monto = Decimal(str(request.data["monto"]))
            if monto <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"error": "monto inválido (debe ser un decimal positivo)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha_pago = date.fromisoformat(request.data["fecha_pago"])
        except (TypeError, ValueError):
            return Response(
                {"error": "fecha_pago inválida (formato esperado YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        metodo_pago = request.data["metodo_pago"]
        valid_metodos = {c.value for c in TeacherPayment.MetodoPago}
        if metodo_pago not in valid_metodos:
            return Response(
                {
                    "error": (
                        f"metodo_pago inválido. Opciones: {sorted(valid_metodos)}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Contrato pertenece al profesor ----
        contract = get_object_or_404(
            TeacherContract,
            pk=request.data["contract"],
            teacher=teacher,
        )

        # ---- Idempotencia: ya existe el pago para ese mes? ----
        if TeacherPayment.objects.filter(
            contract=contract, mes=mes, anio=anio,
        ).exists():
            return Response(
                {
                    "error": (
                        f"Ya existe un pago registrado para {mes:02d}/{anio} "
                        "en este contrato."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Creación atómica: TeacherPayment + CashTransaction ----
        with transaction.atomic():
            payment = TeacherPayment.objects.create(
                contract=contract,
                mes=mes,
                anio=anio,
                monto=monto,
                fecha_pago=fecha_pago,
                metodo_pago=metodo_pago,
                comprobante=request.data.get("comprobante", ""),
                observaciones=request.data.get("observaciones", ""),
            )

            # Categoría sistema "Sueldos" (EGRESO). Idempotente.
            category, _ = CashCategory.objects.get_or_create(
                nombre="Sueldos",
                tipo=CashCategory.Tipo.EGRESO,
                defaults={"es_sistema": True},
            )

            CashTransaction.objects.create(
                categoria=category,
                descripcion=f"Sueldo {teacher} - {payment.mes:02d}/{payment.anio}",
                monto=payment.monto,
                tipo=CashTransaction.Tipo.EGRESO,
                fecha=payment.fecha_pago,
                referencia_teacher_payment=payment,
                creado_por=request.user if request.user.is_authenticated else None,
            )

        return Response(
            TeacherPaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class TeacherContractViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = TeacherContractSerializer

    def get_queryset(self):
        return TeacherContract.objects.filter(
            teacher_id=self.kwargs["teacher_pk"]
        ).prefetch_related("payments")

    def perform_create(self, serializer):
        teacher = get_object_or_404(Teacher, pk=self.kwargs["teacher_pk"])
        serializer.save(teacher=teacher)


class TeacherPaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = TeacherPaymentSerializer

    def get_queryset(self):
        return TeacherPayment.objects.filter(
            contract_id=self.kwargs["contract_pk"],
            contract__teacher_id=self.kwargs["teacher_pk"],
        )

    def perform_create(self, serializer):
        contract = get_object_or_404(
            TeacherContract,
            pk=self.kwargs["contract_pk"],
            teacher_id=self.kwargs["teacher_pk"],
        )
        serializer.save(contract=contract)
