"""API / view tests for reports app."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.classrooms.factories import ClassroomFactory
from apps.payments.factories import PaymentFactory
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestReportViewSet:
    def test_morosidad_excel_download(self, auth_client, admin_user):
        """Test that morosidad report returns an Excel file."""
        current_year = date.today().year
        PaymentFactory(
            estado="VENCIDO",
            anio=current_year,
            fecha_vencimiento=date.today() - timedelta(days=10),
        )

        client = auth_client(admin_user)
        response = client.get(f"/api/v1/reports/morosidad-excel/?anio={current_year}")
        assert response.status_code == 200
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response["Content-Type"]
        )
        assert "attachment" in response["Content-Disposition"]

    def test_alumnos_excel_download(self, auth_client, admin_user):
        """Test that alumnos report returns an Excel file."""
        StudentFactory(estado="ACTIVO")
        StudentFactory(estado="ACTIVO")

        client = auth_client(admin_user)
        response = client.get("/api/v1/reports/alumnos-excel/?estado=ACTIVO")
        assert response.status_code == 200
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response["Content-Type"]
        )

    def test_excel_contains_correct_data(self, auth_client, admin_user):
        """Verify the response is non-empty Excel data."""
        StudentFactory(estado="ACTIVO", nombres="Pepito", apellidos="Flores")

        client = auth_client(admin_user)
        response = client.get("/api/v1/reports/alumnos-excel/?estado=ACTIVO")
        assert response.status_code == 200
        # El endpoint devuelve FileResponse que usa streaming_content
        # (no .content), porque sirve el archivo desde un SpooledTemporaryFile.
        body = b"".join(response.streaming_content)
        assert len(body) > 100  # minimal XLSX size


class TestReportParamValidation:
    """Tests for input validation on report query params."""

    def test_morosidad_invalid_mes(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/reports/morosidad-excel/?mes=13")
        assert response.status_code == 400

    def test_morosidad_invalid_anio(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/reports/morosidad-excel/?anio=abc")
        assert response.status_code == 400

    def test_asistencia_invalid_anio(self, auth_client, admin_user):
        classroom = ClassroomFactory()
        client = auth_client(admin_user)
        response = client.get(
            f"/api/v1/reports/asistencia-excel/?classroom_id={classroom.pk}&anio=xyz"
        )
        assert response.status_code == 400

    def test_cashflow_invalid_mes(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/reports/cashflow-excel/?mes=0")
        assert response.status_code == 400

    def test_cashflow_valid_params(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get(f"/api/v1/reports/cashflow-excel/?anio={date.today().year}")
        assert response.status_code == 200
