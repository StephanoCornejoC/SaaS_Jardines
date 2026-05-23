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


class TestTeacherTipo:
    """Tests para el campo Teacher.tipo (TITULAR / AUXILIAR)."""

    def test_default_tipo_is_titular(self, tenant):
        """Sin especificar tipo, debe ser TITULAR (preserva compatibilidad
        con profesores existentes antes de la migration 0004)."""
        teacher = Teacher.objects.create(
            dni="40000001",
            nombres="Rosa",
            apellidos="Castro",
            telefono="987654321",
            fecha_ingreso=date.today(),
        )
        assert teacher.tipo == "TITULAR"
        assert teacher.tipo == Teacher.Tipo.TITULAR

    def test_can_create_auxiliar(self, tenant):
        """Un profesor puede crearse explícitamente como AUXILIAR."""
        teacher = Teacher.objects.create(
            dni="40000002",
            nombres="Lucia",
            apellidos="Mendoza",
            telefono="987654322",
            tipo=Teacher.Tipo.AUXILIAR,
            fecha_ingreso=date.today(),
        )
        assert teacher.tipo == "AUXILIAR"

    def test_factory_defaults_titular(self, tenant):
        """TeacherFactory respeta el default TITULAR de la factory."""
        teacher = TeacherFactory()
        assert teacher.tipo == "TITULAR"

    def test_factory_override_auxiliar(self, tenant):
        """TeacherFactory acepta override explícito de tipo."""
        teacher = TeacherFactory(tipo="AUXILIAR")
        assert teacher.tipo == "AUXILIAR"

    def test_choices_are_titular_and_auxiliar(self, tenant):
        """Solo se aceptan los dos valores del TextChoices."""
        choices = dict(Teacher._meta.get_field("tipo").choices)
        assert set(choices.keys()) == {"TITULAR", "AUXILIAR"}
        assert choices["TITULAR"] == "Titular"
        assert choices["AUXILIAR"] == "Auxiliar"
