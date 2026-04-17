"""Unit tests for notifications.services."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from apps.notifications.models import EmailLog
from apps.notifications.services import send_attendance_alert, send_payment_reminder
from apps.payments.factories import PaymentFactory
from apps.students.factories import GuardianFactory, StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestSendPaymentReminder:
    @patch("apps.notifications.services.send_mail")
    def test_sends_reminder(self, mock_send_mail, tenant):
        mock_send_mail.return_value = 1

        student = StudentFactory()
        GuardianFactory(student=student, es_principal=True, email="papa@test.com")
        payment = PaymentFactory(
            student=student, mes=3, anio=2026,
            fecha_vencimiento=date(2026, 3, 15),
        )

        log = send_payment_reminder(payment)

        assert log is not None
        assert log.enviado is True
        assert log.tipo == EmailLog.Tipo.RECORDATORIO_PAGO
        assert log.destinatario == "papa@test.com"
        mock_send_mail.assert_called_once()

    def test_returns_none_without_guardian_email(self, tenant):
        student = StudentFactory()
        # Guardian without email
        GuardianFactory(student=student, es_principal=True, email="")
        payment = PaymentFactory(student=student)

        log = send_payment_reminder(payment)
        assert log is None


class TestSendAttendanceAlert:
    @patch("apps.notifications.services.send_mail")
    def test_sends_alert(self, mock_send_mail, tenant):
        mock_send_mail.return_value = 1

        student = StudentFactory()
        GuardianFactory(student=student, es_principal=True, email="mama@test.com")

        log = send_attendance_alert(student, consecutive_absences=3)

        assert log is not None
        assert log.enviado is True
        assert log.tipo == EmailLog.Tipo.ALERTA_ASISTENCIA
        assert "3 inasistencias" in log.contenido

    def test_returns_none_without_guardian(self, tenant):
        student = StudentFactory()
        # No guardian at all

        log = send_attendance_alert(student, consecutive_absences=3)
        assert log is None


class TestEmailLogging:
    @patch("apps.notifications.services.send_mail")
    def test_email_log_created(self, mock_send_mail, tenant):
        mock_send_mail.return_value = 1

        student = StudentFactory()
        GuardianFactory(student=student, es_principal=True, email="log@test.com")
        payment = PaymentFactory(student=student)

        send_payment_reminder(payment)

        assert EmailLog.objects.filter(destinatario="log@test.com").exists()
        log = EmailLog.objects.get(destinatario="log@test.com")
        assert log.enviado is True
        assert log.error == ""

    @patch("apps.notifications.services.send_mail", side_effect=Exception("SMTP Error"))
    def test_failed_email_logged(self, mock_send_mail, tenant):
        student = StudentFactory()
        GuardianFactory(student=student, es_principal=True, email="fail@test.com")
        payment = PaymentFactory(student=student)

        log = send_payment_reminder(payment)

        assert log.enviado is False
        assert "SMTP Error" in log.error
        # The log is still persisted
        assert EmailLog.objects.filter(destinatario="fail@test.com").exists()
