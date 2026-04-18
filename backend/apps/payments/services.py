import io
from datetime import date

import qrcode

from apps.students.models import Student

from .models import MonthlyFee, Payment


def generate_yape_qr(student, payment):
    """
    Genera un codigo QR con la informacion del pago para Yape/Plin.
    Retorna los bytes PNG directamente (sin guardar en filesystem).
    """
    qr_text = (
        f"Pension {student.nombres} {student.apellidos} "
        f"- {payment.mes}/{payment.anio} "
        f"- S/{payment.monto}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


def generate_monthly_payments(anio_escolar, mes):
    """
    Genera registros de Payment para todos los alumnos con MonthlyFee
    activa para el anio_escolar dado, para el mes indicado.
    Retorna la cantidad de pagos creados.
    """
    monthly_fees = MonthlyFee.objects.select_related("student").filter(
        anio_escolar=anio_escolar,
        student__estado=Student.Estado.ACTIVO,
    )

    created_count = 0
    for fee in monthly_fees:
        # Calcular fecha de vencimiento
        try:
            fecha_vencimiento = date(anio_escolar, mes, fee.dia_vencimiento)
        except ValueError:
            # Si el dia no existe en el mes (ej: 31 de febrero), usar ultimo dia
            if mes == 12:
                next_month = date(anio_escolar + 1, 1, 1)
            else:
                next_month = date(anio_escolar, mes + 1, 1)
            from datetime import timedelta

            fecha_vencimiento = next_month - timedelta(days=1)

        _, created = Payment.objects.get_or_create(
            student=fee.student,
            mes=mes,
            anio=anio_escolar,
            defaults={
                "monthly_fee": fee,
                "monto": fee.monto_mensual,
                "fecha_vencimiento": fecha_vencimiento,
                "estado": Payment.Estado.PENDIENTE,
            },
        )
        if created:
            created_count += 1

    return created_count
