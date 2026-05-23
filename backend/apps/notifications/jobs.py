"""
Jobs de notificaciones, ejecutables como funciones planas desde el cron
consolidado `daily_saas_run` o desde tests. No usan Celery.
"""
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def run_payment_reminders_job():
    """Busca pagos pendientes con vencimiento en 3 días y envía recordatorios."""
    from apps.payments.models import Payment
    from apps.notifications.services import send_payment_reminder

    target_date = date.today() + timedelta(days=3)

    payments = Payment.objects.filter(
        estado=Payment.Estado.PENDIENTE,
        fecha_vencimiento=target_date,
    ).select_related("student")

    sent = 0
    errors = 0

    for payment in payments:
        try:
            log = send_payment_reminder(payment)
            if log and log.enviado:
                sent += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            logger.error(f"Error enviando recordatorio para pago {payment.id}: {e}")

    logger.info(
        f"Recordatorios de pago: {sent} enviados, {errors} errores "
        f"(vencimiento: {target_date})"
    )
    return {"enviados": sent, "errores": errors}


def run_attendance_alerts_job():
    """Busca alumnos con 3 o más inasistencias consecutivas y envía alertas."""
    from apps.attendance.models import Attendance
    from apps.students.models import Student
    from apps.notifications.services import send_attendance_alert

    sent = 0
    errors = 0
    threshold = 3

    active_students = Student.objects.filter(
        estado=Student.Estado.ACTIVO,
        attendances__isnull=False,
    ).distinct()

    for student in active_students.iterator():
        recent_list = list(
            Attendance.objects.filter(student=student)
            .order_by("-fecha")
            .values_list("estado", flat=True)[:threshold]
        )

        if len(recent_list) < threshold:
            continue

        consecutive_absences = 0
        for estado in recent_list:
            if estado == Attendance.Estado.AUSENTE:
                consecutive_absences += 1
            else:
                break

        if consecutive_absences >= threshold:
            try:
                log = send_attendance_alert(student, consecutive_absences)
                if log and log.enviado:
                    sent += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                logger.error(
                    f"Error enviando alerta de asistencia para {student}: {e}"
                )

    logger.info(f"Alertas de asistencia: {sent} enviadas, {errors} errores")
    return {"enviados": sent, "errores": errors}
