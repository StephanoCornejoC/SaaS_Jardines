import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import EmailLog

logger = logging.getLogger(__name__)


def _send_and_log(destinatario, asunto, contenido, tipo):
    """Helper interno: envía email y registra en EmailLog."""
    log = EmailLog(
        destinatario=destinatario,
        asunto=asunto,
        contenido=contenido,
        tipo=tipo,
    )
    try:
        send_mail(
            subject=asunto,
            message=contenido,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        log.enviado = True
    except Exception as e:
        log.error = str(e)
        log.enviado = False
        logger.error(f"Error enviando email a {destinatario}: {e}")
    finally:
        log.save()

    return log


def send_payment_reminder(payment):
    """
    Envía recordatorio de pago al apoderado principal del alumno.
    Recibe una instancia de payments.Payment.
    """
    guardian = payment.student.apoderados.filter(
        es_principal=True
    ).exclude(email__isnull=True).exclude(email="").first()

    if not guardian:
        logger.warning(
            f"No se encontró apoderado principal con email para {payment.student}"
        )
        return None

    asunto = f"Recordatorio de pago - {payment.mes}/{payment.anio}"
    contenido = (
        f"Estimado/a {guardian.nombres} {guardian.apellidos},\n\n"
        f"Le recordamos que el pago de la pensión de {payment.student.nombres} "
        f"{payment.student.apellidos} correspondiente al mes {payment.mes}/{payment.anio} "
        f"por el monto de S/ {payment.monto:.2f} tiene fecha de vencimiento "
        f"el {payment.fecha_vencimiento.strftime('%d/%m/%Y')}.\n\n"
        f"Por favor, realice el pago a la brevedad posible.\n\n"
        f"Atentamente,\n"
        f"Administración"
    )

    return _send_and_log(
        destinatario=guardian.email,
        asunto=asunto,
        contenido=contenido,
        tipo=EmailLog.Tipo.RECORDATORIO_PAGO,
    )


def send_attendance_alert(student, consecutive_absences):
    """
    Envía alerta de inasistencias consecutivas al apoderado principal.
    """
    guardian = student.apoderados.filter(
        es_principal=True
    ).exclude(email__isnull=True).exclude(email="").first()

    if not guardian:
        logger.warning(
            f"No se encontró apoderado principal con email para {student}"
        )
        return None

    asunto = f"Alerta de asistencia - {student.nombres} {student.apellidos}"
    contenido = (
        f"Estimado/a {guardian.nombres} {guardian.apellidos},\n\n"
        f"Le informamos que su hijo/a {student.nombres} {student.apellidos} "
        f"tiene {consecutive_absences} inasistencias consecutivas.\n\n"
        f"Le solicitamos comunicarse con la institución para conocer "
        f"la situación académica de su menor.\n\n"
        f"Atentamente,\n"
        f"Administración"
    )

    return _send_and_log(
        destinatario=guardian.email,
        asunto=asunto,
        contenido=contenido,
        tipo=EmailLog.Tipo.ALERTA_ASISTENCIA,
    )


def send_communication_email(communication):
    """
    Envía el contenido de una comunicación a los apoderados relevantes.
    Recibe una instancia de communications.Communication.
    """
    from apps.students.models import Guardian

    guardians_qs = Guardian.objects.filter(
        es_principal=True
    ).exclude(email__isnull=True).exclude(email="")

    if communication.tipo == "POR_AULA" and communication.classroom:
        guardians_qs = guardians_qs.filter(
            student__classroom=communication.classroom,
            student__estado="ACTIVO",
        )
    else:
        guardians_qs = guardians_qs.filter(student__estado="ACTIVO")

    logs = []
    for guardian in guardians_qs.distinct():
        log = _send_and_log(
            destinatario=guardian.email,
            asunto=communication.titulo,
            contenido=communication.contenido,
            tipo=EmailLog.Tipo.COMUNICACION,
        )
        logs.append(log)

    return logs
