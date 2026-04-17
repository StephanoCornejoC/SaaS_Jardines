"""Unit tests for cashflow.models."""

import pytest
from datetime import date
from decimal import Decimal

from apps.cashflow.factories import CashCategoryFactory, CashTransactionFactory
from apps.cashflow.models import CashCategory, CashTransaction, MonthlyClosure

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestCashCategory:
    def test_creation(self, tenant):
        cat = CashCategoryFactory(nombre="Pensiones", tipo="INGRESO")
        assert cat.pk is not None
        assert cat.tipo == "INGRESO"

    def test_str(self, tenant):
        cat = CashCategoryFactory(nombre="Utiles", tipo="EGRESO")
        assert "Utiles" in str(cat)
        assert "Egreso" in str(cat)


class TestCashTransaction:
    def test_creation(self, tenant):
        tx = CashTransactionFactory(monto=Decimal("500.00"))
        assert tx.pk is not None
        assert tx.monto == Decimal("500.00")

    def test_str(self, tenant):
        tx = CashTransactionFactory(descripcion="Pago luz", tipo="EGRESO", monto=Decimal("200.00"))
        result = str(tx)
        assert "Pago luz" in result
        assert "200" in result


class TestMonthlyClosure:
    def test_unique_constraint(self, tenant, admin_user):
        MonthlyClosure.objects.create(
            mes=3, anio=2026,
            total_ingresos=Decimal("1000"),
            total_egresos=Decimal("500"),
            balance=Decimal("500"),
            cerrado_por=admin_user,
        )
        with pytest.raises(Exception):
            MonthlyClosure.objects.create(
                mes=3, anio=2026,
                total_ingresos=Decimal("1000"),
                total_egresos=Decimal("500"),
                balance=Decimal("500"),
                cerrado_por=admin_user,
            )

    def test_str(self, tenant, admin_user):
        closure = MonthlyClosure.objects.create(
            mes=3, anio=2026,
            total_ingresos=Decimal("1000"),
            total_egresos=Decimal("500"),
            balance=Decimal("500"),
            cerrado_por=admin_user,
        )
        assert "3/2026" in str(closure)
