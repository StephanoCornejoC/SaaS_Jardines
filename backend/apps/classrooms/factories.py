"""Factory Boy factories for the classrooms app."""

import factory
from datetime import date


class ClassroomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "classrooms.Classroom"

    nombre = factory.Sequence(lambda n: f"Aula {n}")
    nivel_edad = factory.Iterator([2, 3, 4, 5])
    capacidad = 25
    anio_escolar = factory.LazyFunction(lambda: date.today().year)
    activo = True
