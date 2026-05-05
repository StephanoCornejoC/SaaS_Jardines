from django.core.management.base import BaseCommand

from apps.platform.services import generar_cobros_del_mes


class Command(BaseCommand):
    help = "Genera los cobros mensuales del SaaS para todos los jardines activos."

    def add_arguments(self, parser):
        parser.add_argument("--mes", type=int, default=None)
        parser.add_argument("--anio", type=int, default=None)

    def handle(self, *args, **opts):
        creados = generar_cobros_del_mes(mes=opts.get("mes"), anio=opts.get("anio"))
        self.stdout.write(self.style.SUCCESS(f"Cobros creados: {creados}"))
