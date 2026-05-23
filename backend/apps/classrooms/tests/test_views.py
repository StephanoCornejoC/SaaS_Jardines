"""API / view tests for classrooms app."""

import pytest

from apps.classrooms.factories import ClassroomFactory
from apps.teachers.factories import TeacherFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestClassroomViewSet:
    def test_list_classrooms(self, auth_client, admin_user):
        ClassroomFactory()
        ClassroomFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/classrooms/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_create_classroom_as_admin(self, auth_client, admin_user):
        teacher = TeacherFactory()
        client = auth_client(admin_user)
        data = {
            "nombre": "Estrellitas",
            "nivel_edad": 3,
            "capacidad": 20,
            "profesor_titular": teacher.pk,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 201

    def test_filter_by_nivel(self, auth_client, admin_user):
        ClassroomFactory(nivel_edad=3)
        ClassroomFactory(nivel_edad=5)
        client = auth_client(admin_user)
        response = client.get("/api/v1/classrooms/?nivel_edad=3")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["nivel_edad"] == 3


class TestClassroomTipoValidationsAPI:
    """Tests de regresión para la feature de profesores auxiliares (API)."""

    def test_create_with_titular_and_auxiliar_works(self, auth_client, admin_user):
        """Happy path: crear aula con titular + auxiliar válidos."""
        titular = TeacherFactory(tipo="TITULAR")
        auxiliar = TeacherFactory(tipo="AUXILIAR")
        client = auth_client(admin_user)
        data = {
            "nombre": "Tigritos",
            "nivel_edad": 4,
            "capacidad": 20,
            "profesor_titular": titular.pk,
            "profesor_auxiliar": auxiliar.pk,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 201, response.data
        assert response.data["profesor_auxiliar"] == auxiliar.pk

    def test_create_without_auxiliar_works(self, auth_client, admin_user):
        """El auxiliar es opcional: omitirlo no debe romper la creación."""
        titular = TeacherFactory(tipo="TITULAR")
        client = auth_client(admin_user)
        data = {
            "nombre": "Pinguinos",
            "nivel_edad": 3,
            "capacidad": 20,
            "profesor_titular": titular.pk,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 201, response.data
        assert response.data["profesor_auxiliar"] is None

    def test_create_without_titular_rejected(self, auth_client, admin_user):
        """El titular es obligatorio (regla de negocio del SaaS)."""
        client = auth_client(admin_user)
        data = {
            "nombre": "SinTitular",
            "nivel_edad": 3,
            "capacidad": 20,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 400
        assert "profesor_titular" in response.data

    def test_create_with_auxiliar_as_titular_rejected(self, auth_client, admin_user):
        """Asignar un profesor AUXILIAR al campo profesor_titular falla."""
        auxiliar = TeacherFactory(tipo="AUXILIAR")
        client = auth_client(admin_user)
        data = {
            "nombre": "Confundidos",
            "nivel_edad": 3,
            "capacidad": 20,
            "profesor_titular": auxiliar.pk,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 400
        assert "profesor_titular" in response.data

    def test_create_with_titular_as_auxiliar_rejected(self, auth_client, admin_user):
        """Asignar un profesor TITULAR al campo profesor_auxiliar falla."""
        titular_a = TeacherFactory(tipo="TITULAR")
        titular_b = TeacherFactory(tipo="TITULAR")
        client = auth_client(admin_user)
        data = {
            "nombre": "Confundidos2",
            "nivel_edad": 3,
            "capacidad": 20,
            "profesor_titular": titular_a.pk,
            "profesor_auxiliar": titular_b.pk,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 400
        assert "profesor_auxiliar" in response.data

    def test_list_serializer_exposes_auxiliar(self, auth_client, admin_user):
        """ClassroomListSerializer debe exponer profesor_auxiliar y su nombre.
        Sin esto, el frontend no puede mostrar la columna de auxiliar."""
        titular = TeacherFactory(tipo="TITULAR", nombres="Ana", apellidos="Quispe")
        auxiliar = TeacherFactory(tipo="AUXILIAR", nombres="Beto", apellidos="Soto")
        ClassroomFactory(
            nombre="ConAmbos",
            profesor_titular=titular,
            profesor_auxiliar=auxiliar,
        )
        client = auth_client(admin_user)
        response = client.get("/api/v1/classrooms/?search=ConAmbos")
        assert response.status_code == 200
        results = response.data["results"]
        matching = [r for r in results if r["nombre"] == "ConAmbos"]
        assert matching, "El aula creada no apareció en el listado"
        aula = matching[0]
        assert "profesor_auxiliar" in aula
        assert "profesor_auxiliar_nombre" in aula
        assert aula["profesor_auxiliar"] == auxiliar.pk
