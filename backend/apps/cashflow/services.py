from decimal import Decimal

from django.db.models import Sum

from .models import CashTransaction, MonthlyClosure


def get_balance(mes, anio):
    """
    Calcula el balance (total ingresos - total egresos) para un mes/anio dado.
    Retorna un dict con total_ingresos, total_egresos y balance.
    """
    transactions = CashTransaction.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
    )

    total_ingresos = (
        transactions.filter(tipo=CashTransaction.Tipo.INGRESO).aggregate(
            total=Sum("monto")
        )["total"]
        or Decimal("0.00")
    )

    total_egresos = (
        transactions.filter(tipo=CashTransaction.Tipo.EGRESO).aggregate(
            total=Sum("monto")
        )["total"]
        or Decimal("0.00")
    )

    return {
        "mes": mes,
        "anio": anio,
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "balance": total_ingresos - total_egresos,
    }


def close_month(mes, anio, user):
    """
    Crea un registro de MonthlyClosure con los totales del mes/anio.
    Lanza error si ya existe un cierre para ese mes/anio.
    Retorna el registro de MonthlyClosure creado.
    """
    if MonthlyClosure.objects.filter(mes=mes, anio=anio).exists():
        raise ValueError(f"Ya existe un cierre para {mes}/{anio}")

    balance_data = get_balance(mes, anio)

    closure = MonthlyClosure.objects.create(
        mes=mes,
        anio=anio,
        total_ingresos=balance_data["total_ingresos"],
        total_egresos=balance_data["total_egresos"],
        balance=balance_data["balance"],
        cerrado_por=user,
    )

    return closure


def get_cashflow_summary(anio):
    """
    Retorna un resumen mensual del flujo de caja para el anio dado.
    Retorna una lista con los meses que tienen transacciones y sus totales.
    """
    from django.db.models.functions import ExtractMonth
    from django.db.models import Q

    monthly_data = CashTransaction.objects.filter(
        fecha__year=anio
    ).values(
        mes=ExtractMonth("fecha")
    ).annotate(
        ingresos=Sum("monto", filter=Q(tipo="INGRESO")),
        egresos=Sum("monto", filter=Q(tipo="EGRESO")),
    ).order_by("mes")

    closures = {c.mes: c for c in MonthlyClosure.objects.filter(anio=anio)}

    summary = []
    for month_data in monthly_data:
        mes = month_data["mes"]
        ingresos = month_data["ingresos"] or Decimal("0.00")
        egresos = month_data["egresos"] or Decimal("0.00")
        summary.append({
            "mes": mes,
            "anio": anio,
            "total_ingresos": ingresos,
            "total_egresos": egresos,
            "balance": ingresos - egresos,
            "cerrado": mes in closures,
        })
    return summary
