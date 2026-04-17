"""Unit tests for teachers.models."""

import pytest
from datetime import date
from decimal import Decimal

from apps.teachers.factories import TeacherContractFactory, TeacherFactory, TeacherPaymentFactory
from apps.teachers.models import Teacher, TeacherContract, TeacherPayment

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestTeacherModel:
    def test_creation(self, tenant):
        teacher = TeacherFactory()
        assert teacher.pk is not None
        assert teacher.activo is True

    def test_str(self, tenant):
        teacher = TeacherFactory(nombres="Ana", apellidos="Torres")
        assert str(teacher) == "Torres, Ana"


class TestTeacherContract:
    def test_creation(self, tenant):
        contract = TeacherContractFactory(sueldo=Decimal("3000.00"))
        assert contract.pk is not None
        assert contract.sueldo == Decimal("3000.00")

    def test_str(self, tenant):
        contract = TeacherContractFactory(tipo="MEDIO_TIEMPO")
        assert "Medio tiempo" in str(contract)


class TestTeacherPayment:
    def test_creation(self, tenant):
        payment = TeacherPaymentFactory(mes=4, anio=2026)
        assert payment.pk is not None

    def test_unique_together(self, tenant):
        contract = TeacherContractFactory()
        TeacherPaymentFactory(contract=contract, mes=3, anio=2026)
        with pytest.raises(Exception):
            TeacherPaymentFactory(contract=contract, mes=3, anio=2026)
