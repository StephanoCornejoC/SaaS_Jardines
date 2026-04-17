"""API / view tests for attendance app."""

import pytest
from datetime import date

from apps.attendance.factories import AttendanceFactory
from apps.classrooms.factories import ClassroomFactory
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestAttendanceViewSet:
    def test_registro_masivo(self, auth_client, admin_user):
        classroom = ClassroomFactory()
        s1 = StudentFactory(classroom=classroom)
        s2 = StudentFactory(classroom=classroom)

        client = auth_client(admin_user)
        data = {
            "classroom_id": classroom.pk,
            "fecha": str(date.today()),
            "asistencias": [
                {"student_id": s1.pk, "estado": "PRESENTE"},
                {"student_id": s2.pk, "estado": "AUSENTE"},
            ],
        }
        response = client.post(
            "/api/v1/attendance/registro-masivo/",
            data,
            format="json",
        )
        assert response.status_code == 200
        assert response.data["total"] == 2

    def test_registro_masivo_invalid_student(self, auth_client, admin_user):
        """Students not in the classroom should be rejected."""
        classroom = ClassroomFactory()
        other_student = StudentFactory()  # Not assigned to classroom

        client = auth_client(admin_user)
        data = {
            "classroom_id": classroom.pk,
            "fecha": str(date.today()),
            "asistencias": [
                {"student_id": other_student.pk, "estado": "PRESENTE"},
            ],
        }
        response = client.post(
            "/api/v1/attendance/registro-masivo/",
            data,
            format="json",
        )
        assert response.status_code == 400
        assert "no pertenecen" in response.data.get("detail", "")

    def test_reporte_mensual(self, auth_client, admin_user):
        classroom = ClassroomFactory()
        student = StudentFactory(classroom=classroom)
        today = date.today()

        AttendanceFactory(
            student=student, classroom=classroom,
            fecha=today, estado="PRESENTE",
        )

        client = auth_client(admin_user)
        response = client.get(
            f"/api/v1/attendance/reporte-mensual/"
            f"?classroom_id={classroom.pk}&mes={today.month}&anio={today.year}"
        )
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["total_presentes"] >= 1

    def test_filter_by_classroom(self, auth_client, admin_user):
        c1 = ClassroomFactory()
        c2 = ClassroomFactory()
        AttendanceFactory(classroom=c1, student=StudentFactory(classroom=c1))
        AttendanceFactory(classroom=c2, student=StudentFactory(classroom=c2))

        client = auth_client(admin_user)
        response = client.get(f"/api/v1/attendance/?classroom={c1.pk}")
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["classroom"] == c1.pk

    def test_reporte_missing_params(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/attendance/reporte-mensual/")
        assert response.status_code == 400
