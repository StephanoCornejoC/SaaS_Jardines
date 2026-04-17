"""Unit tests for dashboard.services."""

import pytest
from datetime import date
from decimal import Decimal

from apps.attendance.factories import AttendanceFactory
from apps.cashflow.factories import CashCategoryFactory, CashTransactionFactory
from apps.classrooms.factories import ClassroomFactory
from apps.dashboard.models import DashboardMetric
from apps.dashboard.services import calculate_daily_metrics
from apps.students.factories import StudentFactory
from apps.teachers.factories import TeacherFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestCalculateDailyMetrics:
    def test_creates_metric(self, tenant):
        """calculate_daily_metrics creates a DashboardMetric for today."""
        metric = calculate_daily_metrics()
        assert metric.pk is not None
        assert metric.fecha == date.today()

    def test_counts_alumnos_and_profesores(self, tenant):
        StudentFactory(estado="ACTIVO")
        StudentFactory(estado="ACTIVO")
        StudentFactory(estado="RETIRADO")  # should not count
        TeacherFactory(activo=True)
        TeacherFactory(activo=False)  # should not count

        metric = calculate_daily_metrics()
        assert metric.total_alumnos == 2
        assert metric.total_profesores == 1

    def test_financial_metrics(self, tenant):
        today = date.today()
        cat_i = CashCategoryFactory(tipo="INGRESO")
        cat_e = CashCategoryFactory(tipo="EGRESO")
        CashTransactionFactory(
            categoria=cat_i, tipo="INGRESO",
            monto=Decimal("1000.00"), fecha=today,
        )
        CashTransactionFactory(
            categoria=cat_e, tipo="EGRESO",
            monto=Decimal("300.00"), fecha=today,
        )

        metric = calculate_daily_metrics()
        assert metric.ingresos_mes == Decimal("1000.00")
        assert metric.egresos_mes == Decimal("300.00")
        assert metric.balance_mes == Decimal("700.00")


class TestCalculateDailyMetricsEdgeCases:
    """Edge cases: zero values and division-by-zero protection."""

    def test_zero_transactions(self, tenant):
        """No transactions => ingresos/egresos/balance all 0."""
        metric = calculate_daily_metrics()
        assert metric.ingresos_mes == Decimal("0.00")
        assert metric.egresos_mes == Decimal("0.00")
        assert metric.balance_mes == Decimal("0.00")

    def test_zero_payments_morosidad(self, tenant):
        """No payments this month => morosidad percentage is 0."""
        metric = calculate_daily_metrics()
        assert metric.porcentaje_morosidad == Decimal("0.00")

    def test_zero_attendances(self, tenant):
        """No attendance records => asistencia percentage is 0."""
        metric = calculate_daily_metrics()
        assert metric.porcentaje_asistencia == Decimal("0.00")

    def test_zero_alumnos(self, tenant):
        """No active students => counts are 0."""
        metric = calculate_daily_metrics()
        assert metric.total_alumnos == 0
        assert metric.total_profesores == 0

    def test_updates_existing_metric(self, tenant):
        """Running twice on same day updates the existing metric."""
        m1 = calculate_daily_metrics()
        StudentFactory(estado="ACTIVO")
        m2 = calculate_daily_metrics()
        assert m1.pk == m2.pk
        assert m2.total_alumnos == 1


class TestDashboardViewSet:
    def test_resumen_endpoint(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.get("/api/v1/dashboard/resumen/")
        assert response.status_code == 200
        assert "total_alumnos" in response.data

    def test_historico_endpoint(self, auth_client, admin_user):
        # Create a metric for today
        calculate_daily_metrics()

        client = auth_client(admin_user)
        response = client.get("/api/v1/dashboard/historico/?dias=7")
        assert response.status_code == 200
        assert isinstance(response.data, list)
