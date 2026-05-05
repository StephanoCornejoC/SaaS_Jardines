"""
Management command: notificar_vencimientos

Envía un correo al superadmin con la lista de jardines cuya prueba está
por terminar o cuyo cobro mensual se aproxima.

Pensado para ejecutarse vía cron / scheduler de Railway:
    # Cada día a las 8:00 am
    0 8 * * *  python manage.py notificar_vencimientos

Por defecto avisa con:
  - 7 días de antelación al fin del trial
  - 5 días de antelación al cobro mensual

Configurable con --dias-trial y --dias-cobro.
"""

from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand

from apps.platform.models import TenantSubscription


class Command(BaseCommand):
    help = "Envía correo al superadmin con jardines cuyo trial o cobro vence pronto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias-trial",
            type=int,
            default=7,
            help="Días de antelación para avisar fin de prueba (default 7).",
        )
        parser.add_argument(
            "--dias-cobro",
            type=int,
            default=5,
            help="Días de antelación para avisar cobro mensual (default 5).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=None,
            help="Email destino. Default: SUPERADMIN_EMAIL o ADMINS[0].",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No envía correo, solo muestra qué jardines se incluirían.",
        )

    def handle(self, *args, **options):
        dias_trial = options["dias_trial"]
        dias_cobro = options["dias_cobro"]
        dry_run = options["dry_run"]
        destinatario = options["email"] or self._destinatario()

        if not destinatario:
            self.stderr.write(self.style.ERROR(
                "No hay email destinatario. Configura SUPERADMIN_EMAIL en settings o pasa --email."
            ))
            return

        hoy = date.today()
        # 1) Trials por vencer
        trials = list(self._trials_proximos(hoy, dias_trial))
        # 2) Cobros mensuales por vencer (jardines activos)
        cobros = list(self._cobros_proximos(hoy, dias_cobro))

        if not trials and not cobros:
            self.stdout.write(self.style.SUCCESS(
                f"Sin vencimientos en los próximos {dias_trial}/{dias_cobro} días. "
                "No se envió correo."
            ))
            return

        subject = self._build_subject(trials, cobros)
        text_body, html_body = self._build_body(trials, cobros, dias_trial, dias_cobro, hoy)

        self.stdout.write("Destinatario: " + destinatario)
        self.stdout.write(f"Trials por vencer: {len(trials)}")
        for t in trials:
            self.stdout.write(f"  - {t.tenant.nombre}: trial hasta {t.trial_hasta}")
        self.stdout.write(f"Cobros próximos: {len(cobros)}")
        for c in cobros:
            self.stdout.write(f"  - {c['nombre']}: cobra {c['fecha_cobro']} (S/ {c['monto']})")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY-RUN] No se envió email."))
            return

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Correo enviado a {destinatario}."))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _destinatario(self):
        return (
            getattr(settings, "SUPERADMIN_EMAIL", None)
            or (settings.ADMINS[0][1] if settings.ADMINS else None)
            or settings.DEFAULT_FROM_EMAIL
        )

    def _trials_proximos(self, hoy, dias):
        """Suscripciones en TRIAL cuyo fin esté entre hoy y hoy+dias."""
        limite = hoy + timedelta(days=dias)
        return (
            TenantSubscription.objects.filter(
                estado=TenantSubscription.Estado.TRIAL,
                trial_hasta__gte=hoy,
                trial_hasta__lte=limite,
            )
            .select_related("tenant", "plan")
            .order_by("trial_hasta")
        )

    def _cobros_proximos(self, hoy, dias):
        """Suscripciones ACTIVAS cuyo próximo cobro esté entre hoy y hoy+dias.
        Calcula proximo_cobro en Python (es @property)."""
        activas = (
            TenantSubscription.objects.filter(
                estado__in=[
                    TenantSubscription.Estado.ACTIVA,
                    TenantSubscription.Estado.MOROSA,
                ]
            )
            .select_related("tenant", "plan")
        )
        limite = hoy + timedelta(days=dias)
        out = []
        for sub in activas:
            try:
                fecha = sub.proximo_cobro
            except Exception:
                continue
            if hoy <= fecha <= limite:
                out.append({
                    "nombre": sub.tenant.nombre,
                    "tenant_id": sub.tenant_id,
                    "fecha_cobro": fecha,
                    "monto": sub.precio_acordado,
                    "estado": sub.get_estado_display(),
                })
        out.sort(key=lambda x: x["fecha_cobro"])
        return out

    def _build_subject(self, trials, cobros):
        partes = []
        if trials:
            partes.append(f"{len(trials)} prueba(s)")
        if cobros:
            partes.append(f"{len(cobros)} cobro(s)")
        return "COREM · Próximos vencimientos: " + " y ".join(partes)

    def _build_body(self, trials, cobros, dias_trial, dias_cobro, hoy):
        # Texto plano
        lines = [f"Reporte automático COREM — {hoy.strftime('%d/%m/%Y')}", ""]
        if trials:
            lines.append(f"== Pruebas que terminan en los próximos {dias_trial} días ==")
            for t in trials:
                d = (t.trial_hasta - hoy).days
                lines.append(
                    f"  · {t.tenant.nombre} — trial hasta {t.trial_hasta.strftime('%d/%m/%Y')} "
                    f"(en {d} día{'s' if d != 1 else ''})"
                )
            lines.append("")
        if cobros:
            lines.append(f"== Cobros mensuales en los próximos {dias_cobro} días ==")
            for c in cobros:
                d = (c["fecha_cobro"] - hoy).days
                lines.append(
                    f"  · {c['nombre']} — {c['fecha_cobro'].strftime('%d/%m/%Y')} · "
                    f"S/ {c['monto']} (en {d} día{'s' if d != 1 else ''})"
                )
            lines.append("")
        lines.append("Recuerda contactar a cada cliente para confirmar continuidad.")
        text_body = "\n".join(lines)

        # HTML con formato
        rows_trial = "".join(
            f"<tr><td><strong>{t.tenant.nombre}</strong></td>"
            f"<td>{t.trial_hasta.strftime('%d/%m/%Y')}</td>"
            f"<td style='color:#3b82f6;font-weight:600'>en {(t.trial_hasta - hoy).days} días</td></tr>"
            for t in trials
        )
        rows_cobro = "".join(
            f"<tr><td><strong>{c['nombre']}</strong></td>"
            f"<td>{c['fecha_cobro'].strftime('%d/%m/%Y')}</td>"
            f"<td>S/ {c['monto']}</td>"
            f"<td style='color:#0d9488;font-weight:600'>en {(c['fecha_cobro'] - hoy).days} días</td></tr>"
            for c in cobros
        )

        html_body = f"""
<!DOCTYPE html>
<html lang="es">
<body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f8fafc;padding:24px;color:#0f172a;">
  <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <div style="background:linear-gradient(135deg,#0f766e 0%,#0d9488 100%);color:#fff;padding:18px 24px;">
      <h1 style="margin:0;font-size:18px;font-weight:700;letter-spacing:.3px">COREM SaaS · Próximos vencimientos</h1>
      <p style="margin:4px 0 0;opacity:.85;font-size:13px;">Reporte automático del {hoy.strftime('%d/%m/%Y')}</p>
    </div>
    <div style="padding:22px 24px;">
      {f'''
      <h2 style="font-size:14px;color:#1e40af;margin:0 0 10px;border-bottom:2px solid #dbeafe;padding-bottom:6px">
        Pruebas que terminan en los próximos {dias_trial} días ({len(trials)})
      </h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:18px;">
        <thead><tr style="background:#f1f5f9;text-align:left">
          <th style="padding:8px 10px">Jardín</th>
          <th style="padding:8px 10px">Trial hasta</th>
          <th style="padding:8px 10px">Faltan</th>
        </tr></thead>
        <tbody>{rows_trial}</tbody>
      </table>
      ''' if trials else ''}

      {f'''
      <h2 style="font-size:14px;color:#0f766e;margin:0 0 10px;border-bottom:2px solid #ccfbf1;padding-bottom:6px">
        Cobros mensuales en los próximos {dias_cobro} días ({len(cobros)})
      </h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead><tr style="background:#f1f5f9;text-align:left">
          <th style="padding:8px 10px">Jardín</th>
          <th style="padding:8px 10px">Fecha cobro</th>
          <th style="padding:8px 10px">Monto</th>
          <th style="padding:8px 10px">Faltan</th>
        </tr></thead>
        <tbody>{rows_cobro}</tbody>
      </table>
      ''' if cobros else ''}

      <p style="margin-top:24px;font-size:12px;color:#64748b;">
        Recuerda contactar a cada cliente para confirmar continuidad.
        Este es un mensaje automático — no responder.
      </p>
    </div>
  </div>
</body>
</html>
"""
        return text_body, html_body
