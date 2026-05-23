"""Tests for notification jobs (plain functions, no Celery)."""

import pytest
from datetime import date, timedelta
from unittest.mock import patch

from apps.attendance.factories import AttendanceFactory
from apps.students.factories import StudentFactory
from apps.notifications.jobs import run_attendance_alerts_job

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestRunAttendanceAlertsJob:
    def test_no_students(self, tenant):
        """No active students => no alerts sent."""
        result = run_attendance_alerts_job()
        assert result["enviados"] == 0
        assert result["errores"] == 0

    def test_student_without_attendance(self, tenant):
        """Student with no attendance records => no alert."""
        StudentFactory(estado="ACTIVO")
        result = run_attendance_alerts_job()
        assert result["enviados"] == 0

    def test_student_with_normal_attendance(self, tenant):
        """Student with PRESENTE records => no alert."""
        student = StudentFactory(estado="ACTIVO")
        for i in range(3):
            AttendanceFactory(
                student=student,
                fecha=date.today() - timedelta(days=i),
                estado="PRESENTE",
            )
        result = run_attendance_alerts_job()
        assert result["enviados"] == 0

    @patch("apps.notifications.services.send_attendance_alert")
    def test_student_with_consecutive_absences(self, mock_send, tenant):
        """Student with 3+ consecutive AUSENTE => alert sent."""
        mock_send.return_value = type("Log", (), {"enviado": True})()

        student = StudentFactory(estado="ACTIVO")
        for i in range(3):
            AttendanceFactory(
                student=student,
                fecha=date.today() - timedelta(days=i),
                estado="AUSENTE",
            )
        result = run_attendance_alerts_job()
        assert result["enviados"] == 1
        mock_send.assert_called_once()

    def test_mixed_attendance_no_alert(self, tenant):
        """Student with mixed records (not all AUSENTE) => no alert."""
        student = StudentFactory(estado="ACTIVO")
        AttendanceFactory(student=student, fecha=date.today(), estado="AUSENTE")
        AttendanceFactory(student=student, fecha=date.today() - timedelta(days=1), estado="PRESENTE")
        AttendanceFactory(student=student, fecha=date.today() - timedelta(days=2), estado="AUSENTE")
        result = run_attendance_alerts_job()
        assert result["enviados"] == 0

    def test_inactive_student_ignored(self, tenant):
        """Inactive student with absences => no alert."""
        student = StudentFactory(estado="RETIRADO")
        for i in range(3):
            AttendanceFactory(
                student=student,
                fecha=date.today() - timedelta(days=i),
                estado="AUSENTE",
            )
        result = run_attendance_alerts_job()
        assert result["enviados"] == 0
