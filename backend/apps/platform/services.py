"""Servicios de la plataforma SaaS: cobros, morosidad, métricas."""

from calendar import monthrange
from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.tenants.models import Tenant

from .models import Plan, PlatformCost, PlatformInvoice, TenantSubscription


def _ultimo_dia_mes(anio, mes):
    return date(anio, mes, monthrange(anio, mes)[1])


def generar_cobros_del_mes(mes=None, anio=None, dia_venc=10):
    """
    Genera PlatformInvoice del mes para cada suscripción activa o morosa.
    No genera cobros para suscripciones en TRIAL ni CANCELADAS.
    Idempotente: si ya existe el cobro del periodo, no lo duplica.
    """
    today = date.today()
    mes = mes or today.month
    anio = anio or today.year

    suscripciones = TenantSubscription.objects.filter(
        estado__in=[
            TenantSubscription.Estado.ACTIVA,
            TenantSubscription.Estado.MOROSA,
            TenantSubscription.Estado.BLOQUEADA,
        ],
    ).select_related("tenant")

    # No cobramos a quien aún está en trial
    suscripciones = suscripciones.exclude(
        trial_hasta__gte=date(anio, mes, monthrange(anio, mes)[1])
    )

    creados = 0
    for sub in suscripciones:
        venc = date(anio, mes, min(dia_venc, monthrange(anio, mes)[1]))
        _, was_created = PlatformInvoice.objects.get_or_create(
            tenant=sub.tenant,
            mes=mes,
            anio=anio,
            defaults={
                "monto": sub.precio_acordado,
                "estado": PlatformInvoice.Estado.PENDIENTE,
                "fecha_emision": date(anio, mes, 1),
                "fecha_vencimiento": venc,
            },
        )
        if was_created:
            creados += 1
    return creados


def revisar_morosidad(dias_alerta=3, dias_bloqueo=7):
    """
    Recorre suscripciones y ajusta su estado según las facturas pendientes:
      - factura vencida ≥ dias_bloqueo días → BLOQUEADA
      - factura vencida ≥ dias_alerta días → MOROSA
      - sin facturas vencidas → ACTIVA (o TRIAL si aplica)
    """
    today = date.today()
    cambios = {"bloqueadas": 0, "morosas": 0, "reactivadas": 0}

    for sub in TenantSubscription.objects.exclude(
        estado=TenantSubscription.Estado.CANCELADA
    ).select_related("tenant"):
        # ¿está en trial?
        if sub.trial_hasta and today <= sub.trial_hasta:
            if sub.estado != TenantSubscription.Estado.TRIAL:
                sub.estado = TenantSubscription.Estado.TRIAL
                sub.save(update_fields=["estado", "actualizado_at"])
            continue

        # Factura más vencida no pagada
        peor = (
            PlatformInvoice.objects.filter(
                tenant=sub.tenant,
                estado__in=[
                    PlatformInvoice.Estado.PENDIENTE,
                    PlatformInvoice.Estado.VENCIDA,
                ],
                fecha_vencimiento__lt=today,
            )
            .order_by("fecha_vencimiento")
            .first()
        )

        if not peor:
            if sub.estado != TenantSubscription.Estado.ACTIVA:
                sub.estado = TenantSubscription.Estado.ACTIVA
                sub.save(update_fields=["estado", "actualizado_at"])
                cambios["reactivadas"] += 1
            continue

        dias = (today - peor.fecha_vencimiento).days
        if dias >= dias_bloqueo:
            if sub.estado != TenantSubscription.Estado.BLOQUEADA:
                sub.estado = TenantSubscription.Estado.BLOQUEADA
                sub.save(update_fields=["estado", "actualizado_at"])
                cambios["bloqueadas"] += 1
        elif dias >= dias_alerta:
            if sub.estado != TenantSubscription.Estado.MOROSA:
                sub.estado = TenantSubscription.Estado.MOROSA
                sub.save(update_fields=["estado", "actualizado_at"])
                cambios["morosas"] += 1

        # Marcar factura como VENCIDA si aún figuraba pendiente
        if peor.estado == PlatformInvoice.Estado.PENDIENTE:
            peor.estado = PlatformInvoice.Estado.VENCIDA
            peor.save(update_fields=["estado", "actualizado_at"])

    return cambios


def metricas_dashboard():
    """Calcula los KPIs y series para el dashboard del admin."""
    today = date.today()
    mes_actual = today.month
    anio_actual = today.year

    total_jardines = Tenant.objects.count()
    activos_qs = TenantSubscription.objects.filter(
        estado__in=[
            TenantSubscription.Estado.TRIAL,
            TenantSubscription.Estado.ACTIVA,
            TenantSubscription.Estado.MOROSA,
        ],
    )
    activos = activos_qs.count()
    bloqueados = TenantSubscription.objects.filter(
        estado=TenantSubscription.Estado.BLOQUEADA
    ).count()

    # Plan vigente
    plan = Plan.vigente()
    precio_default = plan.precio_mensual if plan else Decimal("0.00")

    # MRR estimado: suma de precios acordados de suscripciones que ya pasaron trial
    mrr = activos_qs.exclude(trial_hasta__gte=today).aggregate(
        total=Sum("precio_acordado")
    )["total"] or Decimal("0.00")

    # Cobros del mes
    cobros_mes_qs = PlatformInvoice.objects.filter(mes=mes_actual, anio=anio_actual)
    total_a_cobrar = cobros_mes_qs.aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
    cobrado = cobros_mes_qs.filter(
        estado=PlatformInvoice.Estado.PAGADA
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
    pendiente = total_a_cobrar - cobrado

    # Costos del mes
    costos_mes = PlatformCost.objects.filter(
        fecha__month=mes_actual, fecha__year=anio_actual
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")

    margen = cobrado - costos_mes

    # Morosos (factura vencida sin pagar)
    morosos = (
        PlatformInvoice.objects.filter(
            estado__in=[
                PlatformInvoice.Estado.PENDIENTE,
                PlatformInvoice.Estado.VENCIDA,
            ],
            fecha_vencimiento__lt=today,
        )
        .select_related("tenant")
        .order_by("fecha_vencimiento")
    )

    # Serie 12 meses ingresos vs gastos
    series = OrderedDict()
    for offset in range(11, -1, -1):
        m = mes_actual - offset
        a = anio_actual
        while m <= 0:
            m += 12
            a -= 1
        ingresos_m = PlatformInvoice.objects.filter(
            mes=m, anio=a, estado=PlatformInvoice.Estado.PAGADA
        ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        costos_m = PlatformCost.objects.filter(
            fecha__month=m, fecha__year=a
        ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        series[f"{m:02d}/{a}"] = {
            "ingresos": float(ingresos_m),
            "costos": float(costos_m),
            "balance": float(ingresos_m - costos_m),
        }

    # Distribución por estado
    distribucion = (
        TenantSubscription.objects.values("estado")
        .annotate(c=Count("id"))
        .order_by()
    )

    return {
        "total_jardines": total_jardines,
        "activos": activos,
        "bloqueados": bloqueados,
        "precio_default": precio_default,
        "mrr": mrr,
        "total_a_cobrar": total_a_cobrar,
        "cobrado": cobrado,
        "pendiente": pendiente,
        "costos_mes": costos_mes,
        "margen": margen,
        "morosos": morosos[:10],
        "morosos_total": morosos.count(),
        "series": series,
        "distribucion": list(distribucion),
    }
