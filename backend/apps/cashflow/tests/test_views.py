"""API / view tests for cashflow app."""

import pytest
from datetime import date
from decimal import Decimal

from apps.cashflow.factories import CashCategoryFactory, CashTransactionFactory
from apps.cashflow.models import MonthlyClosure

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestCashTransactionViewSet:
    def test_list_transactions(self, auth_client, admin_user):
        CashTransactionFactory()
        CashTransactionFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_create_transaction(self, auth_client, admin_user):
        cat = CashCategoryFactory(tipo="EGRESO")
        client = auth_client(admin_user)
        data = {
            "categoria": cat.pk,
            "descripcion": "Compra de materiales",
            "monto": "150.00",
            "tipo": "EGRESO",
            "fecha": "2026-04-01",
        }
        response = client.post("/api/v1/cashflow/cash-transactions/", data, format="json")
        assert response.status_code == 201
        assert response.data["creado_por"] == admin_user.pk

    def test_filter_by_date_range(self, auth_client, admin_user):
        CashTransactionFactory(fecha=date(2026, 1, 15))
        CashTransactionFactory(fecha=date(2026, 6, 15))
        client = auth_client(admin_user)
        response = client.get(
            "/api/v1/cashflow/cash-transactions/?fecha_desde=2026-01-01&fecha_hasta=2026-03-31"
        )
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["fecha"] <= "2026-03-31"


class TestCashTransactionCloseMonth:
    def test_cerrar_mes(self, auth_client, admin_user):
        CashTransactionFactory(
            tipo="INGRESO",
            monto=Decimal("500.00"),
            fecha=date(2026, 3, 10),
        )
        client = auth_client(admin_user)
        response = client.post(
            "/api/v1/cashflow/cash-transactions/cerrar-mes/",
            {"mes": 3, "anio": 2026},
            format="json",
        )
        assert response.status_code == 201
        assert MonthlyClosure.objects.filter(mes=3, anio=2026).exists()

    def test_cerrar_mes_duplicate(self, auth_client, admin_user):
        client = auth_client(admin_user)
        client.post(
            "/api/v1/cashflow/cash-transactions/cerrar-mes/",
            {"mes": 7, "anio": 2026},
            format="json",
        )
        response = client.post(
            "/api/v1/cashflow/cash-transactions/cerrar-mes/",
            {"mes": 7, "anio": 2026},
            format="json",
        )
        assert response.status_code == 400


class TestResumenAnual:
    def test_resumen_anual(self, auth_client, admin_user):
        CashTransactionFactory(
            tipo="INGRESO",
            monto=Decimal("1000.00"),
            fecha=date(2026, 1, 10),
        )
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/resumen-anual/?anio=2026")
        assert response.status_code == 200
        assert isinstance(response.data, list)


class TestDateValidation:
    """Tests for input validation on date/month/year query params."""

    def test_invalid_fecha_desde(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/?fecha_desde=invalid")
        assert response.status_code == 400

    def test_invalid_fecha_hasta(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/?fecha_hasta=2026-13-45")
        assert response.status_code == 400

    def test_invalid_mes(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/?mes=13")
        assert response.status_code == 400

    def test_invalid_anio(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/?anio=abc")
        assert response.status_code == 400

    def test_invalid_anio_resumen(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/cashflow/cash-transactions/resumen-anual/?anio=notnum")
        assert response.status_code == 400

    def test_valid_params_still_work(self, auth_client, admin_user):
        CashTransactionFactory(fecha=date(2026, 3, 15))
        client = auth_client(admin_user)
        response = client.get(
            "/api/v1/cashflow/cash-transactions/?mes=3&anio=2026"
        )
        assert response.status_code == 200
