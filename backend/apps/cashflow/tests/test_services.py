"""Unit tests for cashflow.services."""

import pytest
from datetime import date
from decimal import Decimal

from apps.cashflow.factories import CashCategoryFactory, CashTransactionFactory
from apps.cashflow.models import MonthlyClosure
from apps.cashflow.services import close_month, get_balance, get_cashflow_summary

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestGetBalance:
    def test_returns_correct_totals(self, tenant):
        cat_ingreso = CashCategoryFactory(tipo="INGRESO")
        cat_egreso = CashCategoryFactory(tipo="EGRESO")

        CashTransactionFactory(
            categoria=cat_ingreso, tipo="INGRESO",
            monto=Decimal("1000.00"), fecha=date(2026, 3, 10),
        )
        CashTransactionFactory(
            categoria=cat_ingreso, tipo="INGRESO",
            monto=Decimal("500.00"), fecha=date(2026, 3, 15),
        )
        CashTransactionFactory(
            categoria=cat_egreso, tipo="EGRESO",
            monto=Decimal("300.00"), fecha=date(2026, 3, 20),
        )

        result = get_balance(3, 2026)
        assert result["total_ingresos"] == Decimal("1500.00")
        assert result["total_egresos"] == Decimal("300.00")
        assert result["balance"] == Decimal("1200.00")

    def test_empty_month_returns_zeros(self, tenant):
        result = get_balance(12, 2030)
        assert result["total_ingresos"] == Decimal("0.00")
        assert result["total_egresos"] == Decimal("0.00")
        assert result["balance"] == Decimal("0.00")


class TestCloseMonth:
    def test_creates_closure(self, tenant, admin_user):
        cat = CashCategoryFactory(tipo="INGRESO")
        CashTransactionFactory(
            categoria=cat, tipo="INGRESO",
            monto=Decimal("800.00"), fecha=date(2026, 4, 5),
        )

        closure = close_month(4, 2026, admin_user)

        assert isinstance(closure, MonthlyClosure)
        assert closure.mes == 4
        assert closure.anio == 2026
        assert closure.total_ingresos == Decimal("800.00")
        assert closure.cerrado_por == admin_user

    def test_duplicate_close_raises(self, tenant, admin_user):
        close_month(5, 2026, admin_user)
        with pytest.raises(ValueError, match="Ya existe un cierre"):
            close_month(5, 2026, admin_user)


class TestGetCashflowSummary:
    def test_aggregation(self, tenant):
        cat_i = CashCategoryFactory(tipo="INGRESO")
        cat_e = CashCategoryFactory(tipo="EGRESO")

        CashTransactionFactory(
            categoria=cat_i, tipo="INGRESO",
            monto=Decimal("1000.00"), fecha=date(2026, 1, 15),
        )
        CashTransactionFactory(
            categoria=cat_e, tipo="EGRESO",
            monto=Decimal("200.00"), fecha=date(2026, 1, 20),
        )
        CashTransactionFactory(
            categoria=cat_i, tipo="INGRESO",
            monto=Decimal("500.00"), fecha=date(2026, 2, 10),
        )

        summary = get_cashflow_summary(2026)

        assert len(summary) >= 2
        jan = next(s for s in summary if s["mes"] == 1)
        assert jan["total_ingresos"] == Decimal("1000.00")
        assert jan["total_egresos"] == Decimal("200.00")
        assert jan["balance"] == Decimal("800.00")
        assert jan["cerrado"] is False
