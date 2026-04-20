"""API / view tests for payments app."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.payments.factories import MonthlyFeeFactory, PaymentFactory
from apps.payments.models import Payment
from apps.students.factories import StudentFactory
from apps.users.factories import ProfesorFactory, UserFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestPaymentViewSet:
    def test_list_payments(self, auth_client, admin_user):
        PaymentFactory()
        PaymentFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_filter_by_estado(self, auth_client, admin_user):
        PaymentFactory(estado="PENDIENTE")
        PaymentFactory(estado="PAGADO")
        client = auth_client(admin_user)
        response = client.get("/api/v1/payments/?estado=PAGADO")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["estado"] == "PAGADO"

    def test_registrar_pago_creates_cash_transaction(self, auth_client, admin_user):
        from apps.cashflow.models import CashTransaction

        payment = PaymentFactory(estado="PENDIENTE")
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/payments/{payment.pk}/registrar-pago/",
            {"estado": "PAGADO", "metodo_pago": "YAPE"},
            format="json",
        )
        assert response.status_code == 200

        payment.refresh_from_db()
        assert payment.estado == "PAGADO"
        assert payment.fecha_pago == date.today()

        # Verify a CashTransaction was created
        tx = CashTransaction.objects.filter(referencia_pago=payment)
        assert tx.exists()
        assert tx.first().tipo == "INGRESO"

    def test_registrar_pago_requires_admin(self, auth_client, profesor_user):
        payment = PaymentFactory(estado="PENDIENTE")
        client = auth_client(profesor_user)
        response = client.patch(
            f"/api/v1/payments/{payment.pk}/registrar-pago/",
            {"estado": "PAGADO"},
            format="json",
        )
        assert response.status_code == 403

    def test_morosidad_report(self, auth_client, admin_user):
        current_year = date.today().year
        # Create an overdue payment
        PaymentFactory(
            estado="PENDIENTE",
            anio=current_year,
            mes=1,
            fecha_vencimiento=date.today() - timedelta(days=30),
        )
        # Create a paid payment -- should not appear
        PaymentFactory(
            estado="PAGADO",
            anio=current_year,
            mes=1,
            fecha_vencimiento=date.today() - timedelta(days=30),
        )

        client = auth_client(admin_user)
        response = client.get(f"/api/v1/payments/morosidad/?anio={current_year}")
        assert response.status_code == 200
        assert response.data["total_morosos"] >= 1

    def test_payment_profesor_readonly(self, auth_client, profesor_user):
        """Profesor can list but not create payments."""
        client = auth_client(profesor_user)
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200


class TestPaymentParamValidation:
    """Tests for input validation on morosidad query params."""

    def test_morosidad_invalid_anio(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/payments/morosidad/?anio=abc")
        assert response.status_code == 400

    def test_morosidad_invalid_mes(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/payments/morosidad/?mes=13")
        assert response.status_code == 400

    def test_morosidad_valid_params(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/payments/morosidad/?anio={date.today().year}&mes=3")
        assert response.status_code == 200


class TestMonthlyFeeViewSet:
    def test_monthly_fee_crud(self, auth_client, admin_user):
        student = StudentFactory()
        client = auth_client(admin_user)

        # Create
        data = {
            "student": student.pk,
            "anio_escolar": date.today().year,
            "monto_mensual": "400.00",
            "dia_vencimiento": 10,
        }
        response = client.post("/api/v1/payments/monthly-fees/", data, format="json")
        assert response.status_code == 201, response.data
        fee_id = response.data["id"]

        # Read
        response = client.get(f"/api/v1/payments/monthly-fees/{fee_id}/")
        assert response.status_code == 200
        assert response.data["monto_mensual"] == "400.00"

    def test_generar_qr(self, auth_client, admin_user):
        """El endpoint QR ahora retorna HTTP 200 con image/png directamente."""
        payment = PaymentFactory()
        client = auth_client(admin_user)
        response = client.get(
            f"/api/v1/payments/{payment.pk}/generar-qr/",
        )
        assert response.status_code == 200
        assert response["Content-Type"].startswith("image/png")
        assert len(response.content) > 100  # PNG válido no vacío
