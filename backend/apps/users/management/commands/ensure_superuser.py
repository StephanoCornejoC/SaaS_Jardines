"""
Crea (o salta) el superusuario SUPERADMIN de la plataforma de forma idempotente
a partir de env vars. Pensado para correr en el startCommand de Railway en
cada deploy: la primera vez crea el user, las siguientes detecta que ya existe
y no hace nada.

Por qué no usamos `createsuperuser --noinput`:
- El comando default de Django no respeta automáticamente el schema `public`
  cuando django-tenants está activo. Si se ejecuta desde un contexto de tenant
  el user termina en el schema equivocado y no se puede iniciar sesión en el Hub.
- Este comando fuerza explicitamente `schema_context("public")` que es donde
  vive la tabla `users_user` (declarada en SHARED_APPS).

Env vars requeridas:
  DJANGO_SUPERUSER_EMAIL       — email del superadmin (USERNAME_FIELD)
  DJANGO_SUPERUSER_PASSWORD    — password en texto plano (se hashea al guardar)
  DJANGO_SUPERUSER_FIRST_NAME  — opcional, default "Super"
  DJANGO_SUPERUSER_LAST_NAME   — opcional, default "Admin"

Comportamiento:
- Si EMAIL o PASSWORD no están seteadas → log warning, exit 0 (no rompe deploy)
- Si el user con ese email YA existe → log info, exit 0 (idempotente)
- Si el user no existe → lo crea con role=SUPERADMIN, is_staff=True, is_superuser=True
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Idempotently ensure the SUPERADMIN user exists, using env vars."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Super").strip()
        last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "Admin").strip()

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                "ensure_superuser: DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD "
                "no estan seteadas. Skipping (no error)."
            ))
            return

        User = get_user_model()

        # Forzar schema public — el User vive en SHARED_APPS
        with schema_context("public"):
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    f"ensure_superuser: el superusuario '{email}' ya existe. Skipping."
                )
                return

            User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(self.style.SUCCESS(
                f"ensure_superuser: superusuario '{email}' creado con role=SUPERADMIN."
            ))
