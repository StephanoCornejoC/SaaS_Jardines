"""Unit tests for students.models."""

import pytest
from datetime import date, timedelta

from apps.classrooms.factories import ClassroomFactory
from apps.students.factories import GuardianFactory, MedicalRecordFactory, StudentFactory
from apps.students.models import Guardian, MedicalRecord, Student

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestStudentModel:
    def test_creation(self, tenant):
        student = StudentFactory()
        assert student.pk is not None
        assert student.estado == "ACTIVO"

    def test_edad_property(self, tenant):
        birth = date.today() - timedelta(days=4 * 365 + 100)
        student = StudentFactory(fecha_nacimiento=birth)
        assert student.edad == 4

    def test_str_representation(self, tenant):
        student = StudentFactory(nombres="Maria", apellidos="Garcia")
        assert str(student) == "Garcia, Maria"

    def test_estado_choices(self, tenant):
        valid_states = [c[0] for c in Student.Estado.choices]
        assert "ACTIVO" in valid_states
        assert "RETIRADO" in valid_states
        assert "EGRESADO" in valid_states


class TestGuardianModel:
    def test_unique_together(self, tenant):
        student = StudentFactory()
        GuardianFactory(student=student, dni="11111111")
        with pytest.raises(Exception):
            GuardianFactory(student=student, dni="11111111")

    def test_str(self, tenant):
        guardian = GuardianFactory(nombres="Carlos", apellidos="Lopez", parentesco="PADRE")
        assert "Lopez, Carlos" in str(guardian)
        assert "Padre" in str(guardian)


class TestMedicalRecord:
    def test_one_to_one(self, tenant):
        student = StudentFactory()
        MedicalRecordFactory(student=student)
        # Creating a second should fail (OneToOne)
        with pytest.raises(Exception):
            MedicalRecordFactory(student=student)

    def test_str(self, tenant):
        student = StudentFactory(nombres="Ana", apellidos="Ruiz")
        record = MedicalRecordFactory(student=student)
        assert "Ana" in str(record) or "Ruiz" in str(record)
