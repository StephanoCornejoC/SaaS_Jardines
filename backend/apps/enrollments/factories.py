"""Factory Boy factories for the enrollments app."""

import factory
from datetime import date
from decimal import Decimal

from apps.students.factories import StudentFactory
from apps.classrooms.factories import ClassroomFactory


class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "enrollments.Enrollment"

    student = factory.SubFactory(StudentFactory)
    classroom = factory.SubFactory(ClassroomFactory)
    anio_escolar = factory.LazyFunction(lambda: date.today().year)
    costo_matricula = Decimal("250.00")
