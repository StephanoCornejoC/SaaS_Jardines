"""Unit tests for classrooms.models."""

import pytest
from datetime import date

from apps.classrooms.factories import ClassroomFactory
from apps.classrooms.models import Classroom
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestClassroomModel:
    def test_creation(self, tenant):
        classroom = ClassroomFactory(nombre="Hormiguitas", nivel_edad=3)
        assert classroom.pk is not None
        assert classroom.nivel_edad == 3

    def test_alumnos_count(self, tenant):
        classroom = ClassroomFactory()
        StudentFactory(classroom=classroom)
        StudentFactory(classroom=classroom)
        assert classroom.alumnos_count == 2

    def test_disponible_property(self, tenant):
        classroom = ClassroomFactory(capacidad=2)
        StudentFactory(classroom=classroom)
        assert classroom.disponible is True

        StudentFactory(classroom=classroom)
        assert classroom.disponible is False

    def test_unique_together(self, tenant):
        current_year = date.today().year
        ClassroomFactory(nombre="Patitos", anio_escolar=current_year)
        with pytest.raises(Exception):
            ClassroomFactory(nombre="Patitos", anio_escolar=current_year)

    def test_str(self, tenant):
        classroom = ClassroomFactory(nombre="Ositos", nivel_edad=4, anio_escolar=2026)
        result = str(classroom)
        assert "Ositos" in result
        assert "4" in result
        assert "2026" in result
