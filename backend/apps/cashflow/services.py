from decimal import Decimal

from django.db.models import Sum

from .models import CashCategory, CashTransaction, MonthlyClosure


# Categorías sistema que cada jardín debe tener al arrancar. Se auto-crean
# vía `ensure_categorias_sistema()` al crear un tenant nuevo. Las marcadas
# como `es_sistema=True` no pueden borrarse desde el admin.
#
# Diseño:
#   - "Pensiones" (INGRESO) y "Sueldos" (EGRESO) ya se auto-crean cuando se
#     registra el primer pago real (payments.views.registrar_pago y
#     teachers.views.registrar_sueldo). Acá las pre-creamos para que
#     aparezcan en el selector del frontend ANTES del primer pago.
#   - "Otros" en ambos tipos cubre cualquier gasto/ingreso que no encaje
#     en las categorías principales (donaciones, eventos, material, etc).
SISTEMA_CATEGORIES = [
    # (nombre, tipo)   — tipo=None significa bidireccional (sirve para
    # INGRESO y EGRESO). Usado para "Otros" que cubre gastos/ingresos
    # varios sin obligar a tener dos categorías separadas.
    ("Pensiones", CashCategory.Tipo.INGRESO),
    ("Sueldos",   CashCategory.Tipo.EGRESO),
    ("Otros",     None),
]


def ensure_categorias_sistema():
    """Garantiza que existan las categorías sistema. Idempotente.

    Debe llamarse DENTRO de un `schema_context(<tenant>)` porque las
    categorías viven en cada schema tenant (TENANT_APPS).
    """
    created = 0
    existing = 0
    for nombre, tipo in SISTEMA_CATEGORIES:
        _, was_created = CashCategory.objects.get_or_create(
            nombre=nombre,
            tipo=tipo,
            defaults={"es_sistema": True, "activo": True},
        )
        if was_created:
            created += 1
        else:
            existing += 1
    return {"created": created, "existing": existing}


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
