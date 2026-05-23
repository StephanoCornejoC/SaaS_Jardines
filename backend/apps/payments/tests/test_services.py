"""Unit tests for payments.services."""

import pytest
from datetime import date

from apps.payments.factories import MonthlyFeeFactory, PaymentFactory
from apps.payments.models import Payment
from apps.payments.services import generate_monthly_payments
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestGenerateMonthlyPayments:
    def test_creates_payment_records(self, tenant):
        """generate_monthly_payments creates Payment for each active student with a fee."""
        current_year = date.today().year
        student1 = StudentFactory(estado="ACTIVO")
        student2 = StudentFactory(estado="ACTIVO")
        MonthlyFeeFactory(student=student1, anio_escolar=current_year)
        MonthlyFeeFactory(student=student2, anio_escolar=current_year)

        count = generate_monthly_payments(current_year, 4)

        assert count == 2
        assert Payment.objects.filter(anio=current_year, mes=4).count() == 2

    def test_skips_existing_payments(self, tenant):
        """Does not duplicate payments if they already exist."""
        current_year = date.today().year
        student = StudentFactory(estado="ACTIVO")
        fee = MonthlyFeeFactory(student=student, anio_escolar=current_year)
        PaymentFactory(student=student, monthly_fee=fee, mes=4, anio=current_year)

        count = generate_monthly_payments(current_year, 4)
        assert count == 0

    def test_skips_inactive_students(self, tenant):
        """Inactive students do not get payments generated."""
        current_year = date.today().year
        student = StudentFactory(estado="RETIRADO")
        MonthlyFeeFactory(student=student, anio_escolar=current_year)

        count = generate_monthly_payments(current_year, 4)
        assert count == 0

    def test_fecha_vencimiento_calculation(self, tenant):
        """The vencimiento date uses the fee's dia_vencimiento."""
        current_year = date.today().year
        student = StudentFactory(estado="ACTIVO")
        MonthlyFeeFactory(
            student=student,
            anio_escolar=current_year,
            dia_vencimiento=20,
        )

        generate_monthly_payments(current_year, 6)
        payment = Payment.objects.get(student=student, mes=6)
        assert payment.fecha_vencimiento == date(current_year, 6, 20)


