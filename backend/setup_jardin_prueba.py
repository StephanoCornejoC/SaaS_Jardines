"""
Setup automatizado de un jardín de prueba para verificar el flujo completo
(roles + permisos + tier banner + módulo cumpleaños) en local.

Idempotente: si el jardín ya existe lo reusa. Las contraseñas son KNOWN
(no random) para facilitar el testing.

Qué crea:
  1. Tenant "Jardín de Prueba" (schema "prueba", dominio "prueba.localhost")
  2. Suscripción Mini con trial de 30 días
  3. User director (ADMIN_JARDIN) con password conocida
  4. Dentro del schema del tenant:
     - 1 Aula "Aula Conejitos" (3 años)
     - 1 Profesora con cuenta de acceso (TEACHER) con password conocida
     - Aula tiene a la profesora como profesora_titular
     - 6 Alumnos en el aula, con fechas de nacimiento variadas:
       * 2 que cumplen este mes (uno hoy, uno en otro día)
       * 2 que cumplen el mes siguiente
       * 2 que cumplen en meses random

Imprime al final un resumen con todas las credenciales.

Ejecutar: ./venv/Scripts/python.exe setup_jardin_prueba.py
"""
import os
from datetime import date, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django_tenants.utils import schema_context

from apps.platform.models import Plan, TenantSubscription
from apps.tenants.models import Domain, Tenant


SCHEMA = "prueba"
DOMINIO = "prueba.localhost"
DIRECTOR_EMAIL = "director@prueba.local"
DIRECTOR_PASSWORD = "Director123!"
PROFESORA_EMAIL = "profesora@prueba.local"
PROFESORA_PASSWORD = "Profesora123!"


def crear_tenant():
    """Crea Tenant + Domain (schema público). Idempotente."""
    tenant, creado = Tenant.objects.get_or_create(
        schema_name=SCHEMA,
        defaults={
            "nombre": "Jardín de Prueba",
            "ruc": "20999999999",
            "email": DIRECTOR_EMAIL,
            "telefono": "999000000",
            "direccion": "Av. Siempre Viva 742, Arequipa",
            "activo": True,
        },
    )
    if creado:
        print(f"  + Tenant '{tenant.nombre}' creado (schema={SCHEMA})")
    else:
        print(f"  = Tenant '{tenant.nombre}' ya existía")

    domain, creado_dom = Domain.objects.get_or_create(
        domain=DOMINIO,
        defaults={"tenant": tenant, "is_primary": True},
    )
    if creado_dom:
        print(f"  + Domain '{DOMINIO}' creado")
    else:
        print(f"  = Domain '{DOMINIO}' ya existía")

    return tenant


def crear_suscripcion(tenant):
    """Crea TenantSubscription con plan Mini. Idempotente."""
    plan_mini = Plan.objects.get(slug="mini", activo=True)
    sub, creado = TenantSubscription.objects.get_or_create(
        tenant=tenant,
        defaults={
            "plan": plan_mini,
            "precio_acordado": plan_mini.precio_mensual,
            "fecha_alta": date.today(),
            "trial_hasta": date.today() + timedelta(days=30),
            "estado": TenantSubscription.Estado.TRIAL,
        },
    )
    if creado:
        print(f"  + Suscripción creada: plan={plan_mini.slug}, "
              f"precio=S/{plan_mini.precio_mensual}, estado=TRIAL")
    else:
        print(f"  = Suscripción ya existía (plan={sub.plan.slug})")
    return sub


def crear_director(tenant):
    """Crea el User director DENTRO DEL SCHEMA DEL TENANT.

    Los users de operación del jardín (ADMIN_JARDIN, TEACHER) viven en el
    schema del tenant porque la tabla users_user está duplicada por schema.
    Solo los SUPERADMIN del panel COREM viven en `public`.
    """
    with schema_context(tenant.schema_name):
        from apps.users.models import User
        user, creado = User.objects.get_or_create(
            email=DIRECTOR_EMAIL,
            defaults={
                "first_name": "María",
                "last_name": "Gómez",
                "role": User.Role.ADMIN_JARDIN,
                "is_staff": True,
                "is_superuser": False,
            },
        )
        user.set_password(DIRECTOR_PASSWORD)
        user.save()
        if creado:
            print(f"  + Director creado: {DIRECTOR_EMAIL} (en schema {tenant.schema_name})")
        else:
            print(f"  = Director ya existía, password reseteado")
    return user


def crear_datos_dentro_del_tenant(tenant):
    """Aula + profesora (con User TEACHER) + 6 alumnos. Idempotente."""
    with schema_context(tenant.schema_name):
        from apps.classrooms.models import Classroom
        from apps.students.models import Guardian, Student
        from apps.teachers.models import Teacher
        from apps.users.models import User

        # --- Aula ---
        aula, creado = Classroom.objects.get_or_create(
            nombre="Conejitos",
            defaults={"nivel_edad": 3, "capacidad": 20},
        )
        if creado:
            print(f"  + Aula 'Conejitos' (3 años) creada")
        else:
            print(f"  = Aula 'Conejitos' ya existía")

        # --- Profesora (Teacher) ---
        profesora, creado_p = Teacher.objects.get_or_create(
            dni="48000001",
            defaults={
                "nombres": "Laura",
                "apellidos": "Mendoza",
                "tipo": Teacher.Tipo.TITULAR,
                "especialidad": "Educación inicial",
                "telefono": "999111222",
                "email": PROFESORA_EMAIL,
                "fecha_ingreso": date.today() - timedelta(days=200),
            },
        )
        if creado_p:
            print(f"  + Profesora 'Laura Mendoza' creada")
        else:
            print(f"  = Profesora ya existía")

        # Asignar la profesora como titular del aula
        if aula.profesor_titular_id != profesora.id:
            aula.profesor_titular = profesora
            aula.save(update_fields=["profesor_titular"])
            print(f"  + Profesora asignada como titular del aula")

        # --- User de la profesora (en el MISMO schema del tenant) ---
        user_prof, creado_u = User.objects.get_or_create(
            email=PROFESORA_EMAIL,
            defaults={
                "first_name": "Laura",
                "last_name": "Mendoza",
                "role": User.Role.TEACHER,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user_prof.set_password(PROFESORA_PASSWORD)
        user_prof.save()
        if creado_u:
            print(f"  + User TEACHER creado: {PROFESORA_EMAIL}")
        else:
            print(f"  = User TEACHER ya existía, password reseteado")

        if profesora.user_id != user_prof.id:
            profesora.user = user_prof
            profesora.save(update_fields=["user"])
            print(f"  + Profesora vinculada al user de login")

        # --- Alumnos ---
        # 6 alumnos con fechas variadas para probar el módulo cumpleaños
        hoy = date.today()
        alumnos_data = [
            # Cumple HOY (para que aparezca el tag "¡Hoy!")
            {
                "dni": "78000001", "nombres": "Mateo", "apellidos": "Quispe",
                "fecha_nacimiento": date(hoy.year - 4, hoy.month, hoy.day),
            },
            # Cumple este mes (otro día)
            {
                "dni": "78000002", "nombres": "Sofía", "apellidos": "Ramírez",
                "fecha_nacimiento": date(hoy.year - 3, hoy.month, max(1, min(28, hoy.day + 5))),
            },
            # Cumple el mes que viene
            {
                "dni": "78000003", "nombres": "Diego", "apellidos": "Flores",
                "fecha_nacimiento": date(hoy.year - 4, (hoy.month % 12) + 1, 10),
            },
            # Cumple el mes que viene
            {
                "dni": "78000004", "nombres": "Valentina", "apellidos": "Salinas",
                "fecha_nacimiento": date(hoy.year - 3, (hoy.month % 12) + 1, 22),
            },
            # Random
            {
                "dni": "78000005", "nombres": "Joaquín", "apellidos": "Torres",
                "fecha_nacimiento": date(hoy.year - 4, 8, 15),
            },
            {
                "dni": "78000006", "nombres": "Camila", "apellidos": "Vargas",
                "fecha_nacimiento": date(hoy.year - 3, 11, 3),
            },
        ]

        for data in alumnos_data:
            alumno, creado_a = Student.objects.get_or_create(
                dni=data["dni"],
                defaults={
                    **data,
                    "genero": Student.Genero.MASCULINO if data["nombres"][-1] == "o" else Student.Genero.FEMENINO,
                    "classroom": aula,
                    "estado": Student.Estado.ACTIVO,
                    "fecha_ingreso": date.today() - timedelta(days=60),
                },
            )
            if creado_a:
                # Apoderado mínimo (requerido en el flujo normal pero acá lo
                # creamos de una)
                Guardian.objects.create(
                    student=alumno,
                    dni=f"4{data['dni'][1:]}",
                    nombres=f"Padre de {data['nombres']}",
                    apellidos=data["apellidos"],
                    telefono="999000000",
                    parentesco=Guardian.Parentesco.PADRE,
                    es_principal=True,
                )

        creados_alumnos = sum(1 for d in alumnos_data
                              if Student.objects.filter(dni=d["dni"]).exists())
        print(f"  + {creados_alumnos} alumnos confirmados en el aula")


def main():
    print("\n" + "=" * 60)
    print("SETUP JARDÍN DE PRUEBA")
    print("=" * 60)

    print("\n[1/3] Schema público — tenant, suscripción, director:")
    tenant = crear_tenant()
    crear_suscripcion(tenant)
    crear_director(tenant)

    print(f"\n[2/3] Dentro del schema '{tenant.schema_name}' — aula, profesora, alumnos:")
    crear_datos_dentro_del_tenant(tenant)

    print("\n[3/3] LISTO. Credenciales:\n")
    print("  Frontend (URL principal de la directora):")
    print(f"    http://{DOMINIO}:3000")
    print()
    print("  Director (ADMIN_JARDIN — ve todo el menú):")
    print(f"    Email:    {DIRECTOR_EMAIL}")
    print(f"    Password: {DIRECTOR_PASSWORD}")
    print()
    print("  Profesora (TEACHER — solo ve Asistencia):")
    print(f"    Email:    {PROFESORA_EMAIL}")
    print(f"    Password: {PROFESORA_PASSWORD}")
    print()
    print("  Admin Django (SUPERADMIN — panel COREM):")
    print("    http://localhost:8000/admin/")
    print()
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
