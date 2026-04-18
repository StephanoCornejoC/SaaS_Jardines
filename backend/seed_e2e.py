"""Seed data para tests E2E - crea tenant, usuarios, aulas, alumnos, etc."""
import os
import django
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.db import connection
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.users.models import User

# ===== 1. Public tenant =====
print("=== Creando public tenant ===")
public, _ = Tenant.objects.get_or_create(
    schema_name="public",
    defaults={"nombre": "Public", "ruc": "00000000000"},
)
Domain.objects.get_or_create(
    domain="localhost",
    tenant=public,
    defaults={"is_primary": True},
)

# ===== 2. Tenant Garabato =====
print("=== Creando tenant Garabato ===")
garabato, created = Tenant.objects.get_or_create(
    schema_name="garabato",
    defaults={"nombre": "Jardin Garabato", "ruc": "20123456789"},
)

# Domains - usamos localhost sin subdominio para pruebas locales
Domain.objects.get_or_create(
    domain="garabato.localhost",
    tenant=garabato,
    defaults={"is_primary": True},
)
# Tambien 127.0.0.1 y localhost:3000 para que funcionen desde diferentes origenes
Domain.objects.get_or_create(
    domain="127.0.0.1",
    tenant=garabato,
    defaults={"is_primary": False},
)

if created:
    print("Tenant creado (schema migrado automaticamente)")
else:
    print("Tenant ya existia")

# ===== 3. Dentro del schema del tenant, crear datos =====
with schema_context("garabato"):
    from apps.users.models import User
    from apps.teachers.models import Teacher
    from apps.classrooms.models import Classroom
    from apps.students.models import Student, Guardian
    from apps.enrollments.models import Enrollment
    from apps.payments.models import MonthlyFee, Payment
    from apps.cashflow.models import CashCategory, CashTransaction
    from apps.communications.models import Communication

    # 3.1 Usuarios
    print("\n=== Creando usuarios ===")
    admin, _ = User.objects.update_or_create(
        email="admin@garabato.com",
        defaults={
            "first_name": "Maria",
            "last_name": "Admin",
            "role": "ADMIN_JARDIN",
            "is_active": True,
        },
    )
    admin.set_password("Admin1234!")
    admin.save()
    print(f"  - {admin.email} / Admin1234!")

    director, _ = User.objects.update_or_create(
        email="director@garabato.com",
        defaults={"first_name": "Carlos", "last_name": "Director", "role": "DIRECTOR", "is_active": True},
    )
    director.set_password("Director1234!")
    director.save()
    print(f"  - {director.email} / Director1234!")

    profe_user, _ = User.objects.update_or_create(
        email="profesor@garabato.com",
        defaults={"first_name": "Ana", "last_name": "Profesora", "role": "PROFESOR", "is_active": True},
    )
    profe_user.set_password("Profesor1234!")
    profe_user.save()
    print(f"  - {profe_user.email} / Profesor1234!")

    # 3.2 Profesores
    print("\n=== Creando profesores ===")
    t1, _ = Teacher.objects.update_or_create(
        dni="40123456",
        defaults={
            "nombres": "Rosa",
            "apellidos": "Castro",
            "especialidad": "Inicial 3 anios",
            "email": "rosa.castro@garabato.com",
            "telefono": "987654321",
            "fecha_ingreso": date(2024, 3, 1),
            "activo": True,
        },
    )
    t2, _ = Teacher.objects.update_or_create(
        dni="40234567",
        defaults={
            "nombres": "Luz",
            "apellidos": "Mendoza",
            "especialidad": "Inicial 4 anios",
            "email": "luz.mendoza@garabato.com",
            "telefono": "987654322",
            "fecha_ingreso": date(2024, 3, 1),
            "activo": True,
        },
    )
    print(f"  - {t1} - {t2}")

    # 3.3 Aulas
    print("\n=== Creando aulas ===")
    aula_3 = Classroom.objects.filter(nombre="Sala Azul").first()
    if not aula_3:
        aula_3 = Classroom.objects.create(
            nombre="Sala Azul",
            nivel_edad=3,
            anio_escolar=2026,
            capacidad=15,
            profesor_titular=t1,
            activo=True,
        )
    aula_4 = Classroom.objects.filter(nombre="Sala Rojitos").first()
    if not aula_4:
        aula_4 = Classroom.objects.create(
            nombre="Sala Rojitos",
            nivel_edad=4,
            anio_escolar=2026,
            capacidad=15,
            profesor_titular=t2,
            activo=True,
        )
    print(f"  - {aula_3} (cap {aula_3.capacidad})")
    print(f"  - {aula_4} (cap {aula_4.capacidad})")

    # 3.4 Alumnos
    print("\n=== Creando alumnos ===")
    alumnos_data = [
        ("71000001", "Juanito", "Perez", date(2023, 5, 10), "M", aula_3),
        ("71000002", "Mariana", "Torres", date(2023, 7, 20), "F", aula_3),
        ("71000003", "Pedro", "Gomez", date(2023, 3, 15), "M", aula_3),
        ("71000004", "Sofia", "Ramirez", date(2022, 1, 5), "F", aula_4),
        ("71000005", "Diego", "Vargas", date(2022, 9, 12), "M", aula_4),
    ]
    alumnos = []
    for dni, nombres, apellidos, fnac, genero, aula in alumnos_data:
        stu, _ = Student.objects.update_or_create(
            dni=dni,
            defaults={
                "nombres": nombres,
                "apellidos": apellidos,
                "fecha_nacimiento": fnac,
                "genero": genero,
                "classroom": aula,
                "estado": "ACTIVO",
                "fecha_ingreso": date(2026, 3, 1),
            },
        )
        alumnos.append(stu)
    print(f"  - {len(alumnos)} alumnos creados")

    # 3.5 Apoderados para el primero
    print("\n=== Creando apoderados ===")
    Guardian.objects.update_or_create(
        student=alumnos[0],
        dni="40999001",
        defaults={
            "nombres": "Elena",
            "apellidos": "Perez Ruiz",
            "telefono": "987111222",
            "email": "elena.perez@email.com",
            "parentesco": "MADRE",
            "es_principal": True,
        },
    )

    # 3.6 Matriculas + Pensiones
    print("\n=== Creando matriculas y pensiones ===")
    categoria_pension, _ = CashCategory.objects.get_or_create(
        nombre="Pensiones",
        tipo="INGRESO",
        defaults={"es_sistema": True},
    )
    categoria_planilla, _ = CashCategory.objects.get_or_create(
        nombre="Planilla",
        tipo="EGRESO",
        defaults={"es_sistema": True},
    )

    for stu in alumnos:
        enr, _ = Enrollment.objects.update_or_create(
            student=stu,
            anio_escolar=2026,
            defaults={
                "classroom": stu.classroom,
                "costo_matricula": Decimal("100.00"),
                "estado": "ACTIVA",
            },
        )
        # Crear monthly fee
        fee, _ = MonthlyFee.objects.update_or_create(
            student=stu,
            anio_escolar=2026,
            defaults={
                "monto_mensual": Decimal("350.00"),
                "dia_vencimiento": 15,
            },
        )
        # Crear 3 pagos: Marzo PAGADO, Abril PENDIENTE, Febrero VENCIDO
        Payment.objects.update_or_create(
            student=stu, mes=3, anio=2026,
            defaults={
                "monthly_fee": fee,
                "monto": Decimal("350.00"),
                "estado": "PAGADO",
                "fecha_vencimiento": date(2026, 3, 15),
                "fecha_pago": date(2026, 3, 10),
                "metodo_pago": "YAPE",
            },
        )
        Payment.objects.update_or_create(
            student=stu, mes=4, anio=2026,
            defaults={
                "monthly_fee": fee,
                "monto": Decimal("350.00"),
                "estado": "PENDIENTE",
                "fecha_vencimiento": date(2026, 4, 15),
            },
        )
        Payment.objects.update_or_create(
            student=stu, mes=2, anio=2026,
            defaults={
                "monthly_fee": fee,
                "monto": Decimal("350.00"),
                "estado": "VENCIDO",
                "fecha_vencimiento": date(2026, 2, 15),
            },
        )

    # 3.7 Transacciones de caja
    print("\n=== Creando transacciones de caja ===")
    CashTransaction.objects.get_or_create(
        descripcion="Pago profesora inglés marzo",
        fecha=date(2026, 3, 28),
        defaults={
            "categoria": categoria_planilla,
            "monto": Decimal("800.00"),
            "tipo": "EGRESO",
            "creado_por": admin,
        },
    )
    CashTransaction.objects.get_or_create(
        descripcion="Pago servicios marzo",
        fecha=date(2026, 3, 5),
        defaults={
            "categoria": categoria_planilla,
            "monto": Decimal("350.00"),
            "tipo": "EGRESO",
            "creado_por": admin,
        },
    )

    # 3.8 Comunicacion de ejemplo
    print("\n=== Creando comunicacion ===")
    Communication.objects.update_or_create(
        titulo="Bienvenidos al año escolar 2026",
        defaults={
            "contenido": "Estimados padres de familia, les damos la bienvenida...",
            "tipo": "GENERAL",
            "enviado": True,
            "enviado_por": admin,
        },
    )

print("\n" + "=" * 50)
print("SEED DATA COMPLETO")
print("=" * 50)
print("\nCredenciales para E2E:")
print("  admin@garabato.com     / Admin1234!     (ADMIN_JARDIN)")
print("  director@garabato.com  / Director1234!  (DIRECTOR)")
print("  profesor@garabato.com  / Profesor1234!  (PROFESOR)")
print("\nTenant: garabato.localhost o 127.0.0.1")
print("Backend URL: http://localhost:8000")
print("=" * 50)
