"""Unit tests for enrollments.models."""

import pytest
from datetime import date
from decimal import Decimal

from apps.enrollments.factories import EnrollmentFactory
from apps.enrollments.models import Enrollment
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestEnrollmentModel:
    def test_creation(self, tenant):
        enrollment = EnrollmentFactory()
        assert enrollment.pk is not None
        assert enrollment.estado == "PENDIENTE"

    def test_unique_together(self, tenant):
        student = StudentFactory()
        year = date.today().year
        EnrollmentFactory(student=student, anio_escolar=year)
        with pytest.raises(Exception):
            EnrollmentFactory(student=student, anio_escolar=year)

    def test_str(self, tenant):
        enrollment = EnrollmentFactory()
        result = str(enrollment)
        assert str(enrollment.anio_escolar) in result
        assert "Pendiente" in result
