"""Servicios de la plataforma SaaS: cobros, morosidad, métricas."""

import logging
from calendar import monthrange
from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Count, Q, Sum

from apps.tenants.models import Tenant

from .models import Plan, PlatformAlert, PlatformCost, PlatformInvoice, TenantSubscription

logger = logging.getLogger(__name__)


_MESES_ES = (
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _build_yape_qr_png(phone, amount, concept):
    """
    Genera un PNG con un QR que contiene un string legible de pago Yape.
    Devuelve bytes del PNG, o None si `qrcode` no está disponible o falta phone.
    """
    if not phone:
        return None
    try:
        import qrcode  # type: ignore
    except ImportError:
        return None
    try:
        payload = f"YAPE | {phone} | S/ {amount:.2f} | {concept}"
        img = qrcode.make(payload)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"No se pudo generar QR Yape: {e}")
        return None


def send_invoice_email(invoice):
    """
    Envía al tenant un email con el cobro mensual del SaaS y un QR Yape
    para pagar (si COREM_YAPE_PHONE está configurado). Si el tenant no
    tiene email, solo logea.
    """
    tenant = invoice.tenant
    destinatario = (tenant.email or "").strip()
    if not destinatario:
        logger.info(f"Tenant {tenant.schema_name} sin email; cobro {invoice.id} no notificado")
        return {"sent": False, "reason": "no email"}

    business = getattr(settings, "COREM_BUSINESS_NAME", "COREM")
    yape = getattr(settings, "COREM_YAPE_PHONE", "")
    plin = getattr(settings, "COREM_PLIN_PHONE", "")

    mes_label = f"{_MESES_ES[invoice.mes]} {invoice.anio}".capitalize()
    concepto = f"{business} - {tenant.nombre} - {invoice.mes:02d}/{invoice.anio}"

    asunto = f"[COREM] Cobro mensual — {mes_label} — S/ {invoice.monto:.2f}"
    cuerpo_txt = (
        f"Hola {tenant.nombre},\n\n"
        f"Le compartimos el cobro mensual de su plataforma COREM correspondiente "
        f"a {mes_label}.\n\n"
        f"Monto: S/ {invoice.monto:.2f}\n"
        f"Vencimiento: {invoice.fecha_vencimiento.strftime('%d/%m/%Y')}\n"
        f"Concepto: {concepto}\n\n"
    )
    if yape:
        cuerpo_txt += f"Yape: {yape}\n"
    if plin:
        cuerpo_txt += f"Plin: {plin}\n"
    if yape:
        cuerpo_txt += "\nPuede escanear el código QR adjunto para pagar por Yape.\n"
    cuerpo_txt += (
        f"\nUna vez realizado el pago, no necesita confirmarlo aquí — "
        f"actualizaremos el estado del cobro automáticamente.\n\n"
        f"Gracias por confiar en {business}.\n"
        f"— Equipo COREM"
    )

    msg = EmailMultiAlternatives(
        subject=asunto,
        body=cuerpo_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario],
    )

    qr_png = _build_yape_qr_png(yape, invoice.monto, concepto) if yape else None
    if qr_png:
        msg.attach(f"yape_{invoice.mes:02d}_{invoice.anio}.png", qr_png, "image/png")

    try:
        msg.send(fail_silently=False)
        logger.info(f"Email de cobro #{invoice.id} enviado a {destinatario}")
        return {"sent": True, "to": destinatario, "qr_attached": bool(qr_png)}
    except Exception as e:
        logger.error(f"Error enviando email de cobro #{invoice.id}: {e}")
        return {"sent": False, "error": str(e)}


def _ultimo_dia_mes(anio, mes):
    return date(anio, mes, monthrange(anio, mes)[1])


def _dia_cobro_efectivo(fecha_alta, anio, mes):
    """
    Día del mes en que se emite el cobro para un tenant cuya fecha de alta
    cayó en `fecha_alta.day`. Si el mes de cobro no tiene ese día (ej: alta
    el 31 y febrero), se usa el último día disponible del mes.
    """
    return min(fecha_alta.day, monthrange(anio, mes)[1])


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

    # Precio de referencia para el dashboard: tomamos el tier Plus como
    # "precio típico" (es el tier que mejor representa el ICP 41-70 alumnos).
    # Antes existía un único Plan global, ahora son 4 tiers y `precio_default`
    # se mantiene solo para compatibilidad del template del dashboard.
    plan_ref = Plan.objects.filter(slug=Plan.SLUG_PLUS, activo=True).first()
    precio_default = plan_ref.precio_mensual if plan_ref else Decimal("0.00")

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


def procesar_trials_vencidos(today=None, dry_run=False):
    """
    Cambia a ACTIVA toda suscripción con estado=TRIAL y trial_hasta < today.
    NO emite cobro (Opción B): el primer cobro se emitirá el día del mes
    igual a fecha_alta (`emitir_cobros_del_dia`).
    """
    today = today or date.today()
    qs = TenantSubscription.objects.filter(
        estado=TenantSubscription.Estado.TRIAL,
        trial_hasta__lt=today,
    ).select_related("tenant")

    finalizados = []
    for sub in qs:
        finalizados.append({
            "tenant": sub.tenant.nombre,
            "schema": sub.tenant.schema_name,
            "trial_hasta": sub.trial_hasta,
        })
        if not dry_run:
            sub.estado = TenantSubscription.Estado.ACTIVA
            sub.save(update_fields=["estado", "actualizado_at"])

    if finalizados:
        logger.info(f"Trials finalizados: {len(finalizados)}")
    return {"count": len(finalizados), "items": finalizados}


def detectar_tier_mismatches(dry_run=False):
    """
    Recorre las suscripciones ACTIVAS y compara el plan asignado contra el
    tier que correspondería según la cantidad actual de alumnos activos.

    Si hay mismatch, asegura que exista una `PlatformAlert` ABIERTA del tipo
    TIER_MISMATCH para ese tenant. Si ya existe una abierta, actualiza su
    contexto y mensaje (no duplica). Si el mismatch se resolvió desde la
    última corrida (el SUPERADMIN cambió el plan a mano), cierra la alerta
    abierta automáticamente.

    NO cambia automáticamente el plan ni envía email a la directora. La
    intervención sigue siendo humana: el SUPERADMIN ve la alerta en el
    admin y coordina con la directora por WhatsApp.

    Returns: {"revisadas": N, "creadas": M, "actualizadas": K, "cerradas": L}
    """
    qs = TenantSubscription.objects.filter(
        estado=TenantSubscription.Estado.ACTIVA,
    ).select_related("tenant", "plan")

    stats = {"revisadas": 0, "creadas": 0, "actualizadas": 0, "cerradas": 0}
    nivel_por_default = PlatformAlert.Nivel.WARNING

    for sub in qs:
        stats["revisadas"] += 1
        tenant = sub.tenant
        try:
            n_alumnos = tenant.alumnos_activos_count()
            tier_correcto = tenant.tier_correcto()
        except Exception as e:
            logger.warning(
                f"No se pudo evaluar tier para tenant {tenant.schema_name}: {e}"
            )
            continue

        if tier_correcto is None:
            continue

        existe_mismatch = sub.plan_id != tier_correcto.id

        alerta_abierta = PlatformAlert.objects.filter(
            tenant=tenant,
            tipo=PlatformAlert.Tipo.TIER_MISMATCH,
            resuelta_at__isnull=True,
        ).first()

        if not existe_mismatch:
            # El plan actual coincide con el tier correcto. Si había una
            # alerta abierta, cerrarla (soporte ya hizo el upgrade).
            if alerta_abierta and not dry_run:
                from django.utils import timezone
                alerta_abierta.resuelta_at = timezone.now()
                alerta_abierta.notas_resolucion = (
                    "Cerrada automáticamente: el plan asignado ya coincide "
                    "con el tier correcto."
                )
                alerta_abierta.save(
                    update_fields=["resuelta_at", "notas_resolucion", "actualizado_at"]
                )
                stats["cerradas"] += 1
            continue

        # Hay mismatch real: crear o actualizar la alerta abierta.
        contexto = {
            "plan_actual_slug": sub.plan.slug if sub.plan else None,
            "plan_actual_nombre": sub.plan.nombre if sub.plan else None,
            "tier_correcto_slug": tier_correcto.slug,
            "tier_correcto_nombre": tier_correcto.nombre,
            "alumnos_activos": n_alumnos,
            "precio_acordado_actual": str(sub.precio_acordado),
            "precio_publico_tier_correcto": str(tier_correcto.precio_mensual),
            "precio_minimo_tier_correcto": str(tier_correcto.precio_minimo),
        }
        direccion = "upgrade" if n_alumnos > (sub.plan.alumnos_max or 10**9) else "downgrade"
        titulo = (
            f"{tenant.nombre}: corresponde {direccion} a {tier_correcto.nombre}"
        )
        mensaje = (
            f"El jardín tiene {n_alumnos} alumnos activos. "
            f"Plan actual: {sub.plan.nombre} (rango {sub.plan.rango_alumnos_texto}). "
            f"Tier correcto: {tier_correcto.nombre} (rango {tier_correcto.rango_alumnos_texto}, "
            f"precio público S/{tier_correcto.precio_mensual}, piso S/{tier_correcto.precio_minimo}). "
            f"Coordinar con la directora por WhatsApp antes de cambiar el plan."
        )

        if dry_run:
            continue

        if alerta_abierta:
            alerta_abierta.contexto = contexto
            alerta_abierta.titulo = titulo
            alerta_abierta.mensaje = mensaje
            alerta_abierta.nivel = nivel_por_default
            alerta_abierta.save(
                update_fields=["contexto", "titulo", "mensaje", "nivel", "actualizado_at"]
            )
            stats["actualizadas"] += 1
        else:
            PlatformAlert.objects.create(
                tenant=tenant,
                tipo=PlatformAlert.Tipo.TIER_MISMATCH,
                nivel=nivel_por_default,
                titulo=titulo,
                mensaje=mensaje,
                contexto=contexto,
            )
            stats["creadas"] += 1

    if stats["creadas"] or stats["actualizadas"] or stats["cerradas"]:
        logger.info(
            f"Tier mismatches: {stats['creadas']} creadas · "
            f"{stats['actualizadas']} actualizadas · {stats['cerradas']} cerradas"
        )
    return stats


def emitir_cobros_del_dia(today=None, dry_run=False, dias_para_vencer=10, send_email=True):
    """
    Emite PlatformInvoice del mes corriente para cada suscripción cuyo
    día de cobro efectivo == today.day (Opción B: día del mes igual a
    fecha_alta, recortado al último día del mes si no existe).

    Idempotente: el unique_together (tenant, mes, anio) más get_or_create
    garantizan que no se duplique. Solo procesa estados ACTIVA y MOROSA.
    Cuando crea un cobro nuevo y send_email=True, envía email al tenant.
    """
    today = today or date.today()
    anio, mes = today.year, today.month

    qs = TenantSubscription.objects.filter(
        estado__in=[
            TenantSubscription.Estado.ACTIVA,
            TenantSubscription.Estado.MOROSA,
        ],
    ).select_related("tenant")

    creados = []
    ya_existian = 0
    emails_enviados = 0
    for sub in qs:
        dia = _dia_cobro_efectivo(sub.fecha_alta, anio, mes)
        if today.day != dia:
            continue
        if dry_run:
            creados.append({
                "tenant": sub.tenant.nombre,
                "schema": sub.tenant.schema_name,
                "monto": float(sub.precio_acordado),
                "would_create": True,
            })
            continue

        venc = _ultimo_dia_mes(anio, mes) if today.day + dias_para_vencer > monthrange(anio, mes)[1] \
            else date(anio, mes, today.day + dias_para_vencer)
        invoice, was_created = PlatformInvoice.objects.get_or_create(
            tenant=sub.tenant,
            mes=mes,
            anio=anio,
            defaults={
                "monto": sub.precio_acordado,
                "estado": PlatformInvoice.Estado.PENDIENTE,
                "fecha_emision": today,
                "fecha_vencimiento": venc,
            },
        )
        if was_created:
            creados.append({
                "tenant": sub.tenant.nombre,
                "schema": sub.tenant.schema_name,
                "invoice_id": invoice.id,
                "monto": float(invoice.monto),
                "fecha_vencimiento": invoice.fecha_vencimiento,
            })
            if send_email:
                result = send_invoice_email(invoice)
                if result.get("sent"):
                    emails_enviados += 1
        else:
            ya_existian += 1

    logger.info(
        f"Cobros emitidos hoy ({today}): {len(creados)} nuevos, "
        f"{ya_existian} ya existían, {emails_enviados} emails enviados"
    )
    return {
        "creados": creados,
        "ya_existian": ya_existian,
        "emails_enviados": emails_enviados,
    }


def emitir_cobro_ahora(tenant, today=None, dias_para_vencer=10, send_email=True):
    """
    Emite el cobro del mes actual para un tenant específico, ignorando el
    chequeo de día_cobro. Útil para el botón "Generar cobro ahora" del admin
    o para casos puntuales (ajustes, demos, recuperación tras error).

    Idempotente vía unique_together. Retorna (invoice, was_created, mensaje).
    Si crea un cobro nuevo y send_email=True, envía email al tenant.
    """
    today = today or date.today()
    sub = TenantSubscription.objects.filter(tenant=tenant).first()
    if not sub:
        return None, False, "El jardín no tiene suscripción asociada."
    if sub.estado in (
        TenantSubscription.Estado.CANCELADA,
        TenantSubscription.Estado.TRIAL,
    ):
        return None, False, (
            f"No se emite cobro: la suscripción está en estado "
            f"{sub.get_estado_display()}."
        )

    anio, mes = today.year, today.month
    venc = _ultimo_dia_mes(anio, mes) if today.day + dias_para_vencer > monthrange(anio, mes)[1] \
        else date(anio, mes, today.day + dias_para_vencer)
    invoice, was_created = PlatformInvoice.objects.get_or_create(
        tenant=tenant,
        mes=mes,
        anio=anio,
        defaults={
            "monto": sub.precio_acordado,
            "estado": PlatformInvoice.Estado.PENDIENTE,
            "fecha_emision": today,
            "fecha_vencimiento": venc,
        },
    )
    if was_created and send_email:
        result = send_invoice_email(invoice)
        sent_msg = (
            " Email enviado." if result.get("sent")
            else f" Email NO enviado ({result.get('reason') or result.get('error')})."
        )
    else:
        sent_msg = ""

    msg = (
        f"Cobro creado: S/ {invoice.monto} (vence {invoice.fecha_vencimiento}).{sent_msg}"
        if was_created
        else f"El cobro de {mes:02d}/{anio} ya existía."
    )
    return invoice, was_created, msg


def notificar_superadmin_resumen(resumen, dry_run=False):
    """
    Envía un email al SUPERADMIN_EMAIL con el resumen del cron diario.
    Si `dry_run=True` o no hay SUPERADMIN_EMAIL configurado, solo logea.
    """
    superadmin_email = getattr(settings, "SUPERADMIN_EMAIL", None)
    if not superadmin_email:
        logger.warning("SUPERADMIN_EMAIL no está configurado; resumen no enviado")
        return {"sent": False, "reason": "no SUPERADMIN_EMAIL"}

    today = date.today()
    trials = resumen.get("trials", {}).get("items", [])
    cobros = resumen.get("cobros", {}).get("creados", [])
    morosidad = resumen.get("morosidad", {})

    asunto = f"[COREM SaaS] Resumen del {today.strftime('%d/%m/%Y')}"
    lineas = [f"Resumen del cron diario — {today.strftime('%d/%m/%Y')}", ""]

    if trials:
        lineas.append(f"Trials finalizados ({len(trials)}):")
        for t in trials:
            lineas.append(f"  - {t['tenant']} (trial hasta {t['trial_hasta']})")
        lineas.append("")
    if cobros:
        total = sum(c["monto"] for c in cobros)
        lineas.append(f"Cobros emitidos hoy ({len(cobros)}, total S/ {total:.2f}):")
        for c in cobros:
            lineas.append(f"  - {c['tenant']}: S/ {c['monto']:.2f} (vence {c['fecha_vencimiento']})")
        lineas.append("")
    if morosidad:
        lineas.append(
            f"Morosidad: {morosidad.get('morosas', 0)} morosas, "
            f"{morosidad.get('bloqueadas', 0)} bloqueadas, "
            f"{morosidad.get('reactivadas', 0)} reactivadas."
        )
        lineas.append("")

    if not (trials or cobros or morosidad.get("morosas") or morosidad.get("bloqueadas")):
        lineas.append("Sin novedades hoy.")

    contenido = "\n".join(lineas)

    if dry_run:
        logger.info(f"[DRY-RUN] notificar_superadmin_resumen → {superadmin_email}\n{contenido}")
        return {"sent": False, "dry_run": True, "preview": contenido}

    try:
        send_mail(
            subject=asunto,
            message=contenido,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[superadmin_email],
            fail_silently=False,
        )
        logger.info(f"Resumen enviado a {superadmin_email}")
        return {"sent": True, "to": superadmin_email}
    except Exception as e:
        logger.error(f"Error enviando resumen al SuperAdmin: {e}")
        return {"sent": False, "error": str(e)}
