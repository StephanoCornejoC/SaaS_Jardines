"""API / view tests for enrollments app."""

import pytest
from datetime import date
from decimal import Decimal

from apps.classrooms.factories import ClassroomFactory
from apps.enrollments.factories import EnrollmentFactory
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestEnrollmentViewSet:
    def test_list_enrollments(self, auth_client, admin_user):
        EnrollmentFactory()
        EnrollmentFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/enrollments/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_create_enrollment_as_admin(self, auth_client, admin_user):
        student = StudentFactory()
        classroom = ClassroomFactory()
        client = auth_client(admin_user)
        data = {
            "student": student.pk,
            "classroom": classroom.pk,
            "anio_escolar": date.today().year,
            "costo_matricula": "250.00",
            "estado": "PENDIENTE",
        }
        response = client.post("/api/v1/enrollments/", data, format="json")
        assert response.status_code == 201

    def test_create_enrollment_as_profesor_forbidden(self, auth_client, profesor_user):
        student = StudentFactory()
        client = auth_client(profesor_user)
        data = {
            "student": student.pk,
            "anio_escolar": date.today().year,
            "costo_matricula": "250.00",
        }
        response = client.post("/api/v1/enrollments/", data, format="json")
        assert response.status_code == 403

    def test_filter_by_anio(self, auth_client, admin_user):
        current_year = date.today().year
        EnrollmentFactory(anio_escolar=current_year)
        EnrollmentFactory(anio_escolar=current_year - 1)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/enrollments/?anio_escolar={current_year}")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["anio_escolar"] == current_year
