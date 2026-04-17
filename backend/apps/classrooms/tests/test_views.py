"""API / view tests for classrooms app."""

import pytest
from datetime import date

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
            "anio_escolar": date.today().year,
            "profesor_titular": teacher.pk,
            "activo": True,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 201

    def test_create_as_profesor_forbidden(self, auth_client, profesor_user):
        client = auth_client(profesor_user)
        data = {
            "nombre": "Forbidden",
            "nivel_edad": 2,
            "capacidad": 15,
            "anio_escolar": date.today().year,
        }
        response = client.post("/api/v1/classrooms/", data, format="json")
        assert response.status_code == 403

    def test_filter_by_nivel(self, auth_client, admin_user):
        ClassroomFactory(nivel_edad=3)
        ClassroomFactory(nivel_edad=5)
        client = auth_client(admin_user)
        response = client.get("/api/v1/classrooms/?nivel_edad=3")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["nivel_edad"] == 3
