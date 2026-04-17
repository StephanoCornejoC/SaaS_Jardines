"""Factory Boy factories for the attendance app."""

import factory
from datetime import date

from apps.students.factories import StudentFactory
from apps.classrooms.factories import ClassroomFactory


class AttendanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "attendance.Attendance"

    student = factory.SubFactory(StudentFactory)
    classroom = factory.SubFactory(ClassroomFactory)
    fecha = factory.LazyFunction(date.today)
    estado = "PRESENTE"
