"""Factory Boy factories for the teachers app."""

import factory
from datetime import date
from decimal import Decimal


class TeacherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "teachers.Teacher"

    dni = factory.Sequence(lambda n: f"{10000000 + n:08d}")
    nombres = factory.Faker("first_name", locale="es")
    apellidos = factory.Faker("last_name", locale="es")
    especialidad = "Educacion Inicial"
    telefono = factory.Sequence(lambda n: f"9{70000000 + n}")
    email = factory.LazyAttribute(lambda o: f"{o.nombres.lower()}.teacher@test.com")
    fecha_ingreso = factory.LazyFunction(date.today)
    activo = True


class TeacherContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "teachers.TeacherContract"

    teacher = factory.SubFactory(TeacherFactory)
    tipo = "TIEMPO_COMPLETO"
    sueldo = Decimal("2500.00")
    fecha_inicio = factory.LazyFunction(date.today)
    activo = True


class TeacherPaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "teachers.TeacherPayment"

    contract = factory.SubFactory(TeacherContractFactory)
    mes = 3
    anio = factory.LazyFunction(lambda: date.today().year)
    monto = Decimal("2500.00")
    fecha_pago = factory.LazyFunction(date.today)
    metodo_pago = "TRANSFERENCIA"
