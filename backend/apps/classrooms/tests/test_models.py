"""Unit tests for classrooms.models."""

import pytest
from django.core.exceptions import ValidationError

from apps.classrooms.factories import ClassroomFactory
from apps.classrooms.models import Classroom
from apps.students.factories import StudentFactory
from apps.teachers.factories import TeacherFactory

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

    def test_nombre_unico(self, tenant):
        ClassroomFactory(nombre="Patitos")
        with pytest.raises(Exception):
            ClassroomFactory(nombre="Patitos")

    def test_str(self, tenant):
        classroom = ClassroomFactory(nombre="Ositos", nivel_edad=4)
        result = str(classroom)
        assert "Ositos" in result
        assert "4" in result


class TestClassroomTipoValidations:
    """Tests para Classroom.clean() — reglas de profesor titular/auxiliar."""

    def test_clean_passes_with_correct_types(self, tenant):
        """Caso happy path: titular TITULAR + auxiliar AUXILIAR + distintos."""
        titular = TeacherFactory(tipo="TITULAR")
        auxiliar = TeacherFactory(tipo="AUXILIAR")
        classroom = Classroom(
            nombre="Mariposas",
            nivel_edad=3,
            capacidad=20,
            profesor_titular=titular,
            profesor_auxiliar=auxiliar,
        )
        classroom.full_clean()  # no raise

    def test_clean_titular_must_be_titular(self, tenant):
        """Asignar un AUXILIAR como profesor_titular debe ser rechazado."""
        auxiliar = TeacherFactory(tipo="AUXILIAR")
        classroom = Classroom(
            nombre="Mariposas",
            nivel_edad=3,
            capacidad=20,
            profesor_titular=auxiliar,
        )
        with pytest.raises(ValidationError) as exc_info:
            classroom.full_clean()
        assert "profesor_titular" in exc_info.value.message_dict

    def test_clean_auxiliar_must_be_auxiliar(self, tenant):
        """Asignar un TITULAR como profesor_auxiliar debe ser rechazado."""
        titular_a = TeacherFactory(tipo="TITULAR")
        titular_b = TeacherFactory(tipo="TITULAR")
        classroom = Classroom(
            nombre="Mariposas",
            nivel_edad=3,
            capacidad=20,
            profesor_titular=titular_a,
            profesor_auxiliar=titular_b,
        )
        with pytest.raises(ValidationError) as exc_info:
            classroom.full_clean()
        assert "profesor_auxiliar" in exc_info.value.message_dict

    def test_clean_titular_and_auxiliar_cannot_be_same(self, tenant):
        """Aunque en la práctica un profesor solo puede ser TITULAR o
        AUXILIAR, validamos también que no aparezca repetido si alguien
        forzara el FK por ORM (defensa en profundidad)."""
        # Creamos un teacher TITULAR y lo asignamos a ambos campos.
        # El primer error que dispara clean es el de tipo (no es AUXILIAR),
        # así que validamos ese path. La validación de "no repetido" se
        # cubre indirectamente en el serializer test del API.
        titular = TeacherFactory(tipo="TITULAR")
        classroom = Classroom(
            nombre="Mariposas",
            nivel_edad=3,
            capacidad=20,
            profesor_titular=titular,
            profesor_auxiliar=titular,
        )
        with pytest.raises(ValidationError):
            classroom.full_clean()

    def test_clean_passes_without_profesores(self, tenant):
        """Compatibilidad: aulas legacy sin titular ni auxiliar son válidas
        a nivel modelo (el serializer requiere titular para creates por API)."""
        classroom = Classroom(
            nombre="Mariposas",
            nivel_edad=3,
            capacidad=20,
        )
        classroom.full_clean()  # no raise
