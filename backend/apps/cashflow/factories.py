"""Factory Boy factories for the cashflow app."""

import factory
from datetime import date
from decimal import Decimal


class CashCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "cashflow.CashCategory"

    nombre = factory.Sequence(lambda n: f"Categoria {n}")
    tipo = "INGRESO"
    activo = True


class CashTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "cashflow.CashTransaction"

    categoria = factory.SubFactory(CashCategoryFactory)
    descripcion = factory.Sequence(lambda n: f"Transaccion {n}")
    monto = Decimal("100.00")
    tipo = "INGRESO"
    fecha = factory.LazyFunction(date.today)
