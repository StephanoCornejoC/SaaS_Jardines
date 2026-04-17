"""Factory Boy factories for the students app."""

import factory
from datetime import date, timedelta


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "students.Student"

    dni = factory.Sequence(lambda n: f"{70000000 + n:08d}")
    nombres = factory.Faker("first_name", locale="es")
    apellidos = factory.Faker("last_name", locale="es")
    fecha_nacimiento = factory.LazyFunction(
        lambda: date.today() - timedelta(days=4 * 365)
    )
    genero = "M"
    estado = "ACTIVO"
    fecha_ingreso = factory.LazyFunction(date.today)


class GuardianFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "students.Guardian"

    student = factory.SubFactory(StudentFactory)
    dni = factory.Sequence(lambda n: f"{40000000 + n:08d}")
    nombres = factory.Faker("first_name", locale="es")
    apellidos = factory.Faker("last_name", locale="es")
    telefono = factory.Sequence(lambda n: f"9{80000000 + n}")
    email = factory.LazyAttribute(lambda o: f"{o.nombres.lower()}@test.com")
    parentesco = "MADRE"
    es_principal = True


class MedicalRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "students.MedicalRecord"

    student = factory.SubFactory(StudentFactory)
    tipo_sangre = "O+"
    alergias = ""
    seguro = "SIS"
    hospital_referencia = "Hospital Nacional"
    contacto_emergencia_nombre = factory.Faker("name", locale="es")
    contacto_emergencia_telefono = "999888777"
