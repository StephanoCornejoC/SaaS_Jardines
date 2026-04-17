"""Factory Boy factories for the payments app."""

import factory
from datetime import date, timedelta
from decimal import Decimal

from apps.students.factories import StudentFactory


class MonthlyFeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.MonthlyFee"

    student = factory.SubFactory(StudentFactory)
    anio_escolar = factory.LazyFunction(lambda: date.today().year)
    monto_mensual = Decimal("350.00")
    dia_vencimiento = 15


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.Payment"

    student = factory.SubFactory(StudentFactory)
    monthly_fee = factory.SubFactory(
        MonthlyFeeFactory,
        student=factory.SelfAttribute("..student"),
    )
    mes = 3
    anio = factory.LazyFunction(lambda: date.today().year)
    monto = Decimal("350.00")
    estado = "PENDIENTE"
    fecha_vencimiento = factory.LazyFunction(
        lambda: date.today() + timedelta(days=15)
    )
