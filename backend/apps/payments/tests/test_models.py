"""Unit tests for payments.models."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.payments.factories import MonthlyFeeFactory, PaymentFactory
from apps.payments.models import MonthlyFee, Payment
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestPaymentModel:
    def test_payment_creation(self, tenant):
        payment = PaymentFactory()
        assert payment.pk is not None
        assert payment.estado == "PENDIENTE"
        assert payment.monto == Decimal("350.00")

    def test_payment_default_estado(self, tenant):
        payment = PaymentFactory()
        assert payment.estado == Payment.Estado.PENDIENTE

    def test_payment_is_overdue_when_past_due(self, tenant):
        payment = PaymentFactory(
            fecha_vencimiento=date.today() - timedelta(days=1),
            estado="PENDIENTE",
        )
        assert payment.is_overdue is True

    def test_payment_is_not_overdue_when_paid(self, tenant):
        payment = PaymentFactory(
            fecha_vencimiento=date.today() - timedelta(days=1),
            estado="PAGADO",
        )
        assert payment.is_overdue is False

    def test_payment_is_not_overdue_when_exonerado(self, tenant):
        payment = PaymentFactory(
            fecha_vencimiento=date.today() - timedelta(days=1),
            estado="EXONERADO",
        )
        assert payment.is_overdue is False

    def test_payment_unique_per_student_month(self, tenant):
        student = StudentFactory()
        PaymentFactory(student=student, mes=3, anio=2026)
        with pytest.raises(Exception):
            PaymentFactory(student=student, mes=3, anio=2026)


class TestMonthlyFeeModel:
    def test_monthly_fee_creation(self, tenant):
        fee = MonthlyFeeFactory()
        assert fee.pk is not None
        assert fee.monto_mensual == Decimal("350.00")

    def test_unique_constraint(self, tenant):
        student = StudentFactory()
        MonthlyFeeFactory(student=student, anio_escolar=2026)
        with pytest.raises(Exception):
            MonthlyFeeFactory(student=student, anio_escolar=2026)

    def test_monthly_fee_str(self, tenant):
        fee = MonthlyFeeFactory()
        result = str(fee)
        assert "S/" in result
        assert str(fee.anio_escolar) in result
