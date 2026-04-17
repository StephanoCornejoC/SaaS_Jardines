"""Unit tests for attendance.models."""

import pytest
from datetime import date

from apps.attendance.factories import AttendanceFactory
from apps.attendance.models import Attendance
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestAttendanceModel:
    def test_creation(self, tenant):
        att = AttendanceFactory()
        assert att.pk is not None
        assert att.estado == "PRESENTE"

    def test_unique_together(self, tenant):
        student = StudentFactory()
        today = date.today()
        AttendanceFactory(student=student, fecha=today)
        with pytest.raises(Exception):
            AttendanceFactory(student=student, fecha=today)

    def test_str(self, tenant):
        att = AttendanceFactory(estado="TARDANZA")
        result = str(att)
        assert "Tardanza" in result
