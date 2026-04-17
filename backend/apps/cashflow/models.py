from django.conf import settings
from django.db import models


class CashCategory(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    tipo = models.CharField(max_length=7, choices=Tipo.choices, verbose_name="Tipo")
    es_sistema = models.BooleanField(
        default=False,
        verbose_name="Es categoría de sistema",
        help_text="Categorías generadas automáticamente por el sistema",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tipo", "nombre"]
        verbose_name = "Categoría de caja"
        verbose_name_plural = "Categorías de caja"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class CashTransaction(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    categoria = models.ForeignKey(
        CashCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Categoría",
    )
    descripcion = models.CharField(max_length=300, verbose_name="Descripción")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    tipo = models.CharField(max_length=7, choices=Tipo.choices, verbose_name="Tipo")
    fecha = models.DateField(verbose_name="Fecha")
    referencia_pago = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_transactions",
        verbose_name="Pago vinculado",
    )
    referencia_teacher_payment = models.ForeignKey(
        "teachers.TeacherPayment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_transactions",
        verbose_name="Pago de profesor vinculado",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_transactions",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-created_at"]
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descripcion} (S/{self.monto})"


class MonthlyClosure(models.Model):
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    total_ingresos = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total ingresos"
    )
    total_egresos = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total egresos"
    )
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Balance"
    )
    cerrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="monthly_closures",
        verbose_name="Cerrado por",
    )
    observaciones = models.TextField(blank=True)
    fecha_cierre = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de cierre")

    class Meta:
        unique_together = ("mes", "anio")
        ordering = ["-anio", "-mes"]
        verbose_name = "Cierre mensual"
        verbose_name_plural = "Cierres mensuales"

    def __str__(self):
        return f"Cierre {self.mes}/{self.anio} - Balance: S/{self.balance}"
