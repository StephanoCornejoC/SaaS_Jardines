"""API / view tests for teachers app."""

import pytest
from datetime import date
from decimal import Decimal

from apps.cashflow.models import CashCategory, CashTransaction
from apps.teachers.factories import (
    TeacherContractFactory,
    TeacherFactory,
    TeacherPaymentFactory,
)
from apps.teachers.models import TeacherPayment
from apps.users.factories import UserFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestTeacherViewSet:
    def test_list_teachers(self, auth_client, admin_user):
        TeacherFactory()
        TeacherFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_search_by_name(self, auth_client, admin_user):
        TeacherFactory(nombres="Gabriela", apellidos="Mistral")
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/?search=Gabriela")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_teacher_as_admin(self, auth_client, admin_user):
        client = auth_client(admin_user)
        data = {
            "dni": "88776655",
            "nombres": "Nuevo",
            "apellidos": "Profesor",
            "especialidad": "Musica",
            "telefono": "999222333",
            "fecha_ingreso": str(date.today()),
        }
        response = client.post("/api/v1/teachers/", data, format="json")
        assert response.status_code == 201

    def test_teacher_detail_with_contracts(self, auth_client, admin_user):
        teacher = TeacherFactory()
        TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/teachers/{teacher.pk}/")
        assert response.status_code == 200


class TestSueldosEndpoint:
    """Tests del endpoint GET /teachers/<id>/sueldos/?anio=Y.

    Devuelve contrato activo + pagos del año. Si no hay contrato activo, 400.
    """

    def test_returns_payments_for_year(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(
            teacher=teacher, sueldo=Decimal("3000.00"), activo=True,
        )
        TeacherPaymentFactory(
            contract=contract, mes=3, anio=2026, monto=Decimal("3000.00"),
        )
        TeacherPaymentFactory(
            contract=contract, mes=4, anio=2026, monto=Decimal("3000.00"),
        )
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/teachers/{teacher.pk}/sueldos/?anio=2026")
        assert response.status_code == 200, response.data
        data = response.data
        assert data["anio"] == 2026
        assert data["sueldo_mensual"] == "3000.00"
        assert data["meses_pagados"] == 2
        assert data["meses_pendientes"] == 10
        assert data["total_pagado"] == "6000.00"
        assert len(data["pagos"]) == 2
        assert data["contract"]["id"] == contract.id

    def test_no_active_contract_returns_400(self, auth_client, admin_user):
        teacher = TeacherFactory()
        # Solo contratos inactivos
        TeacherContractFactory(teacher=teacher, activo=False)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/teachers/{teacher.pk}/sueldos/")
        assert response.status_code == 400
        assert "contrato activo" in response.data["error"]

    def test_default_year_is_current(self, auth_client, admin_user):
        teacher = TeacherFactory()
        TeacherContractFactory(teacher=teacher, activo=True)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/teachers/{teacher.pk}/sueldos/")
        assert response.status_code == 200
        assert response.data["anio"] == date.today().year


class TestRegistrarSueldoEndpoint:
    """Tests del endpoint POST /teachers/<id>/registrar-sueldo/.

    Critico: debe crear TeacherPayment Y CashTransaction EGRESO vinculados
    en una transacción atómica.
    """

    def _payload(self, contract, **overrides):
        base = {
            "contract": contract.id,
            "mes": 3,
            "anio": 2026,
            "monto": "3000.00",
            "fecha_pago": str(date(2026, 3, 5)),
            "metodo_pago": "TRANSFERENCIA",
            "comprobante": "OP-12345",
            "observaciones": "Pago de marzo",
        }
        base.update(overrides)
        return base

    def test_creates_payment_and_cashtransaction(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher, sueldo=Decimal("3000.00"))
        client = auth_client(admin_user)

        assert TeacherPayment.objects.count() == 0
        assert CashTransaction.objects.count() == 0

        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract),
            format="json",
        )
        assert response.status_code == 201, response.data
        assert TeacherPayment.objects.count() == 1
        assert CashTransaction.objects.count() == 1

    def test_cashtransaction_links_to_teacher_payment(self, auth_client, admin_user):
        """La FK referencia_teacher_payment debe quedar seteada."""
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher, sueldo=Decimal("2500.00"))
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, monto="2500.00"),
            format="json",
        )
        assert response.status_code == 201

        payment = TeacherPayment.objects.get()
        tx = CashTransaction.objects.get()
        assert tx.referencia_teacher_payment_id == payment.id
        assert tx.tipo == CashTransaction.Tipo.EGRESO
        assert tx.monto == Decimal("2500.00")
        assert tx.fecha == date(2026, 3, 5)

    def test_category_sueldos_is_system(self, auth_client, admin_user):
        """La categoría 'Sueldos' se crea con es_sistema=True para que la
        directora no la borre accidentalmente."""
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract),
            format="json",
        )
        assert response.status_code == 201
        cat = CashCategory.objects.get(nombre="Sueldos")
        assert cat.tipo == CashCategory.Tipo.EGRESO
        assert cat.es_sistema is True

    def test_uses_input_amount_not_contract_salary(self, auth_client, admin_user):
        """El monto del request manda — permite registrar bonos o ajustes
        sin tocar el sueldo base del contrato."""
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher, sueldo=Decimal("2000.00"))
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, monto="2500.00"),
            format="json",
        )
        assert response.status_code == 201
        payment = TeacherPayment.objects.get()
        assert payment.monto == Decimal("2500.00")  # del request, no del contrato
        tx = CashTransaction.objects.get()
        assert tx.monto == Decimal("2500.00")

    def test_duplicate_month_rejected(self, auth_client, admin_user):
        """Idempotencia: no se puede registrar 2 veces el mismo mes/año."""
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher)
        TeacherPaymentFactory(contract=contract, mes=3, anio=2026)
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, mes=3, anio=2026),
            format="json",
        )
        assert response.status_code == 400
        assert "Ya existe" in response.data["error"]
        # No se duplicó: sigue habiendo 1 payment y 0 transactions
        assert TeacherPayment.objects.count() == 1
        assert CashTransaction.objects.count() == 0

    def test_missing_fields_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            {"mes": 3, "anio": 2026},  # falta contract, monto, fecha_pago, metodo_pago
            format="json",
        )
        assert response.status_code == 400
        assert "Faltan campos requeridos" in response.data["error"]

    def test_invalid_mes_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, mes=13),
            format="json",
        )
        assert response.status_code == 400

    def test_invalid_metodo_pago_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, metodo_pago="BITCOIN"),
            format="json",
        )
        assert response.status_code == 400

    def test_negative_amount_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/teachers/{teacher.pk}/registrar-sueldo/",
            self._payload(contract, monto="-100.00"),
            format="json",
        )
        assert response.status_code == 400


class TestActualizarSueldoEndpoint:
    """Tests del endpoint PATCH /teachers/<id>/actualizar-sueldo/.

    Crítico para UX: la directora cambia el sueldo de un profe desde el
    módulo Profesores sin tener que pedirle a Stephano que entre al admin.
    """

    def test_updates_active_contract(self, auth_client, admin_user):
        teacher = TeacherFactory()
        contract = TeacherContractFactory(
            teacher=teacher, sueldo=Decimal("1500.00"),
            tipo="TIEMPO_COMPLETO", activo=True,
        )
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {"sueldo": "1800.00"},
            format="json",
        )
        assert response.status_code == 200, response.data
        assert response.data["created"] is False
        contract.refresh_from_db()
        assert contract.sueldo == Decimal("1800.00")

    def test_creates_contract_if_none(self, auth_client, admin_user):
        """Si el profesor no tiene contrato activo, el endpoint lo crea
        con los datos mínimos para que el sueldo quede registrado."""
        teacher = TeacherFactory()
        assert teacher.contracts.count() == 0
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {"sueldo": "2000.00"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["created"] is True
        assert teacher.contracts.count() == 1
        contract = teacher.contracts.get()
        assert contract.sueldo == Decimal("2000.00")
        assert contract.tipo == "TIEMPO_COMPLETO"  # default
        assert contract.activo is True

    def test_accepts_custom_tipo_contrato(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {"sueldo": "1000.00", "tipo_contrato": "MEDIO_TIEMPO"},
            format="json",
        )
        assert response.status_code == 200
        assert teacher.contracts.get().tipo == "MEDIO_TIEMPO"

    def test_missing_sueldo_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {},
            format="json",
        )
        assert response.status_code == 400

    def test_negative_sueldo_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {"sueldo": "-500.00"},
            format="json",
        )
        assert response.status_code == 400

    def test_invalid_tipo_rejected(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/teachers/{teacher.pk}/actualizar-sueldo/",
            {"sueldo": "1500.00", "tipo_contrato": "FREELANCE"},
            format="json",
        )
        assert response.status_code == 400


class TestTeacherListSerializerWithSueldo:
    """El listado expone sueldo_actual + contrato_id + tipo_contrato."""

    def test_includes_sueldo_actual(self, auth_client, admin_user):
        teacher = TeacherFactory()
        TeacherContractFactory(
            teacher=teacher, sueldo=Decimal("1750.00"), activo=True,
        )
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/")
        assert response.status_code == 200
        match = [r for r in response.data["results"] if r["id"] == teacher.id]
        assert match
        assert match[0]["sueldo_actual"] == "1750.00"
        assert match[0]["contrato_id"] is not None
        assert match[0]["tipo_contrato"] == "TIEMPO_COMPLETO"

    def test_sueldo_null_if_no_active_contract(self, auth_client, admin_user):
        teacher = TeacherFactory()
        TeacherContractFactory(teacher=teacher, activo=False)
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/")
        assert response.status_code == 200
        match = [r for r in response.data["results"] if r["id"] == teacher.id]
        assert match
        assert match[0]["sueldo_actual"] is None
        assert match[0]["contrato_id"] is None
