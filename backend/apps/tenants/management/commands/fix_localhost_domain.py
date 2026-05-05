"""
Management command: fix_localhost_domain

Cambia el dominio 'localhost' para que apunte al schema 'public' en lugar de
al tenant garabato. Esto permite acceder al panel del superadmin desde
localhost:8000/admin/ directamente, sin confusión con public.localhost.

El frontend del jardín sigue funcionando porque usa 127.0.0.1:3000 (no localhost).

Uso:
    python manage.py fix_localhost_domain
    python manage.py fix_localhost_domain --add-public-localhost  (crea también public.localhost si no existe)
"""

from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Domain, Tenant


class Command(BaseCommand):
    help = "Mueve el dominio 'localhost' al schema public para el admin del superadmin"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué haría sin ejecutar cambios",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # 1. Obtener el tenant público
        try:
            public_tenant = Tenant.objects.get(schema_name="public")
        except Tenant.DoesNotExist:
            raise CommandError("No existe un tenant con schema_name='public'.")

        self.stdout.write(f"Tenant público encontrado: {public_tenant.schema_name} (id={public_tenant.id})")

        # 2. Buscar dominio 'localhost'
        try:
            domain = Domain.objects.select_related("tenant").get(domain="localhost")
        except Domain.DoesNotExist:
            self.stdout.write(self.style.WARNING("No existe registro para 'localhost'. Creando uno nuevo..."))
            if not dry_run:
                Domain.objects.create(domain="localhost", tenant=public_tenant, is_primary=False)
                self.stdout.write(self.style.SUCCESS("Dominio 'localhost' creado apuntando a schema 'public'."))
            else:
                self.stdout.write("[DRY-RUN] Crearía Domain(domain='localhost', tenant=public, is_primary=False)")
            return

        tenant_anterior = domain.tenant.schema_name
        if domain.tenant_id == public_tenant.id:
            self.stdout.write(self.style.SUCCESS("'localhost' ya apunta al schema 'public'. No hay cambios."))
            return

        self.stdout.write(
            f"'localhost' actualmente apunta a schema '{tenant_anterior}'. "
            f"Se moverá a schema 'public'."
        )

        if dry_run:
            self.stdout.write("[DRY-RUN] No se ejecutaron cambios.")
            return

        domain.tenant = public_tenant
        domain.is_primary = False
        domain.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Dominio 'localhost' movido de '{tenant_anterior}' a 'public'.\n"
                f"Ahora accede al admin del superadmin en: http://localhost:8000/admin/"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "El frontend del jardín debe seguir usando http://127.0.0.1:3000 (no localhost:3000)."
            )
        )
