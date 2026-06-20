"""
Quita is_staff / is_superuser a los usuarios ADMIN_JARDIN y TEACHER en todos
los schemas de jardín.

Esos roles operan por la app (API DRF con su rol), NO por el admin de Django.
Tener is_staff/is_superuser les permitía entrar al admin y, vía
/admin/op/<otro-schema>/, operar el jardín de otro cliente (hallazgo de
seguridad C1). El gate del admin ya exige rol SUPERADMIN, pero este comando
aplica además el principio de mínimo privilegio sobre los datos existentes.

Uso:
    python manage.py fix_user_privileges --dry-run   # preview, no escribe
    python manage.py fix_user_privileges             # aplica los cambios
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django_tenants.utils import get_tenant_model, schema_context


class Command(BaseCommand):
    help = (
        "Quita is_staff/is_superuser a usuarios ADMIN_JARDIN/TEACHER en todos "
        "los jardines (mínimo privilegio; cierra el hallazgo C1)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué cambiaría sin escribir en la base.",
        )

    def handle(self, *args, **options):
        from apps.users.models import User

        dry = options["dry_run"]
        Tenant = get_tenant_model()
        total = 0

        for tenant in Tenant.objects.exclude(schema_name__in=("public", "info")):
            with schema_context(tenant.schema_name):
                qs = User.objects.filter(
                    role__in=[User.Role.ADMIN_JARDIN, User.Role.TEACHER],
                ).filter(Q(is_staff=True) | Q(is_superuser=True))
                for u in qs:
                    self.stdout.write(
                        f"[{tenant.schema_name}] {u.email}: "
                        f"is_staff {u.is_staff}->False, "
                        f"is_superuser {u.is_superuser}->False"
                    )
                    if not dry:
                        u.is_staff = False
                        u.is_superuser = False
                        u.save(update_fields=["is_staff", "is_superuser"])
                    total += 1

        prefix = "(dry-run) " if dry else ""
        self.stdout.write(
            self.style.SUCCESS(f"{prefix}{total} usuario(s) ajustado(s).")
        )
