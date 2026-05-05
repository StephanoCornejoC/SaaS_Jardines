"""API / view tests for teachers app."""

import pytest
from datetime import date

from apps.teachers.factories import TeacherContractFactory, TeacherFactory
from apps.users.factories import UserFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestTeacherViewSet:
    def test_list_teachers(self, auth_client, admin_user):
        TeacherFactory()
        TeacherFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_search_by_name(self, auth_client, admin_user):
        TeacherFactory(nombres="Gabriela", apellidos="Mistral")
        client = auth_client(admin_user)
        response = client.get("/api/v1/teachers/?search=Gabriela")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_teacher_as_admin(self, auth_client, admin_user):
        client = auth_client(admin_user)
        data = {
            "dni": "88776655",
            "nombres": "Nuevo",
            "apellidos": "Profesor",
            "especialidad": "Musica",
            "telefono": "999222333",
            "fecha_ingreso": str(date.today()),
        }
        response = client.post("/api/v1/teachers/", data, format="json")
        assert response.status_code == 201

    def test_create_teacher_as_profesor_forbidden(self, auth_client, profesor_user):
        client = auth_client(profesor_user)
        data = {
            "dni": "11223344",
            "nombres": "Forbidden",
            "apellidos": "Teacher",
            "telefono": "999000111",
            "fecha_ingreso": str(date.today()),
        }
        response = client.post("/api/v1/teachers/", data, format="json")
        assert response.status_code == 403

    def test_teacher_detail_with_contracts(self, auth_client, admin_user):
        teacher = TeacherFactory()
        TeacherContractFactory(teacher=teacher)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/teachers/{teacher.pk}/")
        assert response.status_code == 200
