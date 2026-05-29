"""
Comando consolidado del cron diario del SaaS COREM.

Diseño:
- Un solo arranque de Django al día (~30-60s) en lugar de N crons separados.
- Sin Celery ni Redis — funciones planas invocadas en orden.
- Idempotente: se puede re-ejecutar sin duplicar cobros ni emails.
- Soporta --dry-run para validar sin escribir nada.

Pasos en orden:
  1. Trials vencidos → ACTIVA (Opción B: NO emite cobro al cambiar de estado)
  2. Emisión de cobros del día (cuando today.day == fecha_alta.day del tenant)
     · Genera PlatformInvoice idempotente
     · Envía email con QR Yape al tenant si su email está configurado
  3. Revisión de morosidad (3 días → MOROSA, 7 días → BLOQUEADA)
  4. Email al SUPERADMIN_EMAIL con el resumen del día (schema público)
  5. Recordatorios de pago + alertas de asistencia POR TENANT (schema_context)

CONFIGURACIÓN EN RAILWAY:
  En el dashboard de Railway, crea un nuevo servicio (o cron job) apuntando
  al mismo repo + DB:
    Build: usa el Dockerfile existente
    Start command:  python manage.py daily_saas_run
    Cron schedule:  0 13 * * *      (8:00 AM Lima = 13:00 UTC)

  Variables de entorno necesarias para que todo funcione bien:
    DJANGO_SETTINGS_MODULE   = config.settings.prod
    DJANGO_SECRET_KEY        = (mismo del web service)
    PG*                      = (mismas credenciales que el web service)
    DEFAULT_FROM_EMAIL       = noreply@corem.pe
    SUPERADMIN_EMAIL         = (tu email para recibir el resumen)
    EMAIL_HOST_USER / PASSWORD = (SMTP)
    COREM_YAPE_PHONE         = (opcional, para incluir QR en el email de cobro)
    COREM_PLIN_PHONE         = (opcional)
    COREM_BUSINESS_NAME      = (opcional, default "COREM Labs S.A.C.")

  PRUEBA EN PROD ANTES DE DEJARLO AUTOMÁTICO:
    Ejecuta una vez `python manage.py daily_saas_run --dry-run` desde la consola
    del servicio para confirmar que arranca sin escribir nada.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import schema_context

from apps.platform.services import (
    detectar_tier_mismatches,
    emitir_cobros_del_dia,
    notificar_superadmin_resumen,
    procesar_trials_vencidos,
    revisar_morosidad,
)
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Cron diario consolidado del SaaS: trials, cobros, morosidad y notificaciones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecuta sin escribir cambios; solo logea lo que haría.",
        )
        parser.add_argument(
            "--skip-tenant-jobs",
            action="store_true",
            help="Omite los jobs por tenant (recordatorios de pago, alertas de asistencia).",
        )

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        skip_tenant_jobs = opts["skip_tenant_jobs"]

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.MIGRATE_HEADING(f"{prefix}daily_saas_run inicia"))

        # Pasos 1-4 corren en el schema público (donde viven platform.*)
        with schema_context("public"):
            trials = procesar_trials_vencidos(dry_run=dry_run)
            self.stdout.write(f"  Trials finalizados: {trials['count']}")

            cobros = emitir_cobros_del_dia(dry_run=dry_run)
            self.stdout.write(
                f"  Cobros emitidos: {len(cobros['creados'])} nuevos · "
                f"{cobros['ya_existian']} ya existían"
            )

            if dry_run:
                morosidad = {"bloqueadas": 0, "morosas": 0, "reactivadas": 0}
                self.stdout.write("  Morosidad: omitida en dry-run (cambia estados)")
            else:
                morosidad = revisar_morosidad()
                self.stdout.write(
                    f"  Morosidad: {morosidad['morosas']} morosas · "
                    f"{morosidad['bloqueadas']} bloqueadas · "
                    f"{morosidad['reactivadas']} reactivadas"
                )

            # Detección de mismatches de tier: tenants cuyo plan asignado no
            # coincide con el tier que correspondería según alumnos activos.
            # Sin envío de email — solo genera alertas internas para soporte.
            mismatches = detectar_tier_mismatches(dry_run=dry_run)
            self.stdout.write(
                f"  Tier mismatches: {mismatches['revisadas']} suscripciones revisadas · "
                f"{mismatches['creadas']} alertas nuevas · "
                f"{mismatches['actualizadas']} actualizadas · "
                f"{mismatches['cerradas']} cerradas"
            )

            resumen = {
                "trials": trials,
                "cobros": cobros,
                "morosidad": morosidad,
                "tier_mismatches": mismatches,
            }
            notif = notificar_superadmin_resumen(resumen, dry_run=dry_run)
            if notif.get("sent"):
                self.stdout.write(f"  Resumen enviado a {notif['to']}")
            elif notif.get("dry_run"):
                self.stdout.write("  Resumen: dry-run, no enviado")
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Resumen NO enviado: {notif.get('reason') or notif.get('error')}"
                ))

        # Paso 5: jobs por tenant. Cada uno dentro de su schema_context.
        if skip_tenant_jobs:
            self.stdout.write("  Jobs por tenant: omitidos por --skip-tenant-jobs")
        else:
            self._run_per_tenant_jobs(dry_run)

        self.stdout.write(self.style.SUCCESS(f"{prefix}daily_saas_run completado"))

    def _run_per_tenant_jobs(self, dry_run):
        """Itera tenants no-public y corre payment reminders + attendance alerts."""
        from apps.notifications.jobs import (
            run_attendance_alerts_job,
            run_payment_reminders_job,
        )

        tenants = Tenant.objects.exclude(schema_name__in=("public", "info"))
        total_recordatorios = 0
        total_alertas = 0
        for tenant in tenants:
            self.stdout.write(f"  → {tenant.schema_name} ({tenant.nombre})")
            if dry_run:
                self.stdout.write("      dry-run: jobs por tenant omitidos")
                continue
            try:
                with schema_context(tenant.schema_name):
                    r = run_payment_reminders_job()
                    a = run_attendance_alerts_job()
                total_recordatorios += r.get("enviados", 0)
                total_alertas += a.get("enviados", 0)
                self.stdout.write(
                    f"      recordatorios: {r['enviados']} · alertas: {a['enviados']}"
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"      Error en tenant {tenant.schema_name}: {e}"
                ))

        self.stdout.write(
            f"  Totales jobs por tenant: {total_recordatorios} recordatorios · "
            f"{total_alertas} alertas"
        )
