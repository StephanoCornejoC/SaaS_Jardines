from django.core.management.base import BaseCommand

from apps.platform.services import revisar_morosidad


class Command(BaseCommand):
    help = "Revisa cobros vencidos y ajusta el estado de cada suscripción (MOROSA / BLOQUEADA)."

    def handle(self, *args, **opts):
        cambios = revisar_morosidad()
        self.stdout.write(self.style.SUCCESS(
            f"Bloqueadas: {cambios['bloqueadas']} · "
            f"Morosas: {cambios['morosas']} · "
            f"Reactivadas: {cambios['reactivadas']}"
        ))
