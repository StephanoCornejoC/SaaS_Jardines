"""API / view tests for students app."""

import pytest
from datetime import date

from apps.classrooms.factories import ClassroomFactory
from apps.students.factories import GuardianFactory, MedicalRecordFactory, StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestStudentViewSet:
    def test_list_students(self, auth_client, admin_user):
        StudentFactory()
        StudentFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/students/")
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_search_by_name(self, auth_client, admin_user):
        StudentFactory(nombres="Juanito", apellidos="Perez")
        StudentFactory(nombres="Maria", apellidos="Lopez")
        client = auth_client(admin_user)
        response = client.get("/api/v1/students/?search=Juanito")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["nombres"] == "Juanito"

    def test_filter_by_estado(self, auth_client, admin_user):
        StudentFactory(estado="ACTIVO")
        StudentFactory(estado="RETIRADO")
        client = auth_client(admin_user)
        response = client.get("/api/v1/students/?estado=RETIRADO")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["estado"] == "RETIRADO"

    def test_create_student_as_admin(self, auth_client, admin_user):
        classroom = ClassroomFactory()
        client = auth_client(admin_user)
        data = {
            "dni": "99887766",
            "nombres": "Nuevo",
            "apellidos": "Alumno",
            "fecha_nacimiento": "2021-06-15",
            "genero": "F",
            "estado": "ACTIVO",
            "fecha_ingreso": str(date.today()),
            "classroom": classroom.pk,
        }
        response = client.post("/api/v1/students/", data, format="json")
        assert response.status_code == 201

    def test_create_student_as_profesor_forbidden(self, auth_client, profesor_user):
        client = auth_client(profesor_user)
        data = {
            "dni": "11223344",
            "nombres": "Forbidden",
            "apellidos": "Student",
            "fecha_nacimiento": "2021-01-01",
            "genero": "M",
            "estado": "ACTIVO",
            "fecha_ingreso": str(date.today()),
        }
        response = client.post("/api/v1/students/", data, format="json")
        assert response.status_code == 403

    def test_student_detail_includes_apoderados(self, auth_client, admin_user):
        student = StudentFactory()
        GuardianFactory(student=student)
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/students/{student.pk}/")
        assert response.status_code == 200
        assert "apoderados" in response.data
        assert len(response.data["apoderados"]) == 1

    def test_guardian_crud(self, auth_client, admin_user):
        student = StudentFactory()
        client = auth_client(admin_user)

        # Create guardian
        data = {
            "dni": "55667788",
            "nombres": "Guardian",
            "apellidos": "Nuevo",
            "telefono": "999111222",
            "parentesco": "PADRE",
            "es_principal": True,
        }
        response = client.post(
            f"/api/v1/students/{student.pk}/guardians/",
            data,
            format="json",
        )
        assert response.status_code == 201

        # List guardians
        response = client.get(f"/api/v1/students/{student.pk}/guardians/")
        assert response.status_code == 200

    def test_medical_record_crud(self, auth_client, admin_user):
        student = StudentFactory()
        client = auth_client(admin_user)

        # Create medical record
        data = {
            "tipo_sangre": "A+",
            "alergias": "Polen",
            "seguro": "SIS",
            "hospital_referencia": "Hospital Rebagliati",
            "contacto_emergencia_nombre": "Mama",
            "contacto_emergencia_telefono": "999888777",
        }
        response = client.post(
            f"/api/v1/students/{student.pk}/medical-record/",
            data,
            format="json",
        )
        assert response.status_code == 201
