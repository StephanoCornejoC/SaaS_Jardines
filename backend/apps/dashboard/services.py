import logging
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum

logger = logging.getLogger(__name__)


def calculate_daily_metrics():
    """
    Calcula las métricas del día y crea/actualiza el DashboardMetric correspondiente.
    """
    from apps.attendance.models import Attendance
    from apps.cashflow.models import CashTransaction
    from apps.dashboard.models import DashboardMetric
    from apps.payments.models import Payment
    from apps.students.models import Student
    from apps.teachers.models import Teacher

    today = date.today()
    current_month = today.month
    current_year = today.year

    # Total alumnos activos
    total_alumnos = Student.objects.filter(estado=Student.Estado.ACTIVO).count()

    # Total profesores activos
    total_profesores = Teacher.objects.filter(activo=True).count()

    # Alumnos por nivel de edad
    alumnos_por_nivel = {}
    nivel_counts = (
        Student.objects.filter(estado=Student.Estado.ACTIVO, classroom__isnull=False)
        .values("classroom__nivel_edad")
        .annotate(total=Count("id"))
    )
    for item in nivel_counts:
        nivel = item["classroom__nivel_edad"]
        alumnos_por_nivel[f"{nivel}_anios"] = item["total"]

    # Ingresos y egresos del mes (desde cashflow)
    transactions_mes = CashTransaction.objects.filter(
        fecha__month=current_month,
        fecha__year=current_year,
    )
    ingresos_mes = transactions_mes.filter(
        tipo=CashTransaction.Tipo.INGRESO
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")

    egresos_mes = transactions_mes.filter(
        tipo=CashTransaction.Tipo.EGRESO
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")

    balance_mes = ingresos_mes - egresos_mes

    # Porcentaje de morosidad
    total_pagos_mes = Payment.objects.filter(
        mes=current_month, anio=current_year
    ).count()
    pagos_vencidos = Payment.objects.filter(
        mes=current_month,
        anio=current_year,
        estado=Payment.Estado.VENCIDO,
    ).count()
    porcentaje_morosidad = Decimal("0.00")
    if total_pagos_mes > 0:
        porcentaje_morosidad = Decimal(
            str(round(pagos_vencidos / total_pagos_mes * 100, 2))
        )

    # Porcentaje de asistencia del mes
    total_asistencias = Attendance.objects.filter(
        fecha__month=current_month,
        fecha__year=current_year,
    ).count()
    total_presentes = Attendance.objects.filter(
        fecha__month=current_month,
        fecha__year=current_year,
        estado=Attendance.Estado.PRESENTE,
    ).count()
    porcentaje_asistencia = Decimal("0.00")
    if total_asistencias > 0:
        porcentaje_asistencia = Decimal(
            str(round(total_presentes / total_asistencias * 100, 2))
        )

    # Crear o actualizar métrica
    metric, created = DashboardMetric.objects.update_or_create(
        fecha=today,
        defaults={
            "total_alumnos": total_alumnos,
            "total_profesores": total_profesores,
            "alumnos_por_nivel": alumnos_por_nivel,
            "ingresos_mes": ingresos_mes,
            "egresos_mes": egresos_mes,
            "balance_mes": balance_mes,
            "porcentaje_morosidad": porcentaje_morosidad,
            "porcentaje_asistencia": porcentaje_asistencia,
        },
    )

    action = "creada" if created else "actualizada"
    logger.info(f"Métrica del dashboard {action} para {today}")

    return metric
