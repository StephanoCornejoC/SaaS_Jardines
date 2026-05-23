from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MonthlyFee(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="monthly_fees",
        verbose_name="Alumno",
    )
    anio_escolar = models.IntegerField(verbose_name="Año escolar")
    monto_mensual = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Monto mensual"
    )
    dia_vencimiento = models.PositiveIntegerField(
        default=15,
        help_text="Dia del mes para vencimiento",
        verbose_name="Día de vencimiento",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "anio_escolar")
        ordering = ["-anio_escolar", "student__apellidos"]
        verbose_name = "Pensión mensual"
        verbose_name_plural = "Pensiones mensuales"

    def __str__(self):
        return f"{self.student} - {self.anio_escolar} (S/{self.monto_mensual})"


class Payment(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        VENCIDO = "VENCIDO", "Vencido"
        EXONERADO = "EXONERADO", "Exonerado"

    class MetodoPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        YAPE = "YAPE", "Yape"
        PLIN = "PLIN", "Plin"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        OTRO = "OTRO", "Otro"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Alumno",
    )
    monthly_fee = models.ForeignKey(
        MonthlyFee,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Pensión mensual",
    )
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Mes",
    )
    anio = models.IntegerField(verbose_name="Año")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de pago")
    metodo_pago = models.CharField(
        max_length=15,
        choices=MetodoPago.choices,
        blank=True,
        verbose_name="Método de pago",
    )
    comprobante = models.CharField(max_length=200, blank=True, verbose_name="Comprobante")
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_registered",
        verbose_name="Registrado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "mes", "anio")
        ordering = ["-anio", "-mes", "student__apellidos"]
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"{self.student} - {self.mes}/{self.anio} ({self.get_estado_display()})"

    @property
    def is_overdue(self):
        if self.estado in (self.Estado.PAGADO, self.Estado.EXONERADO):
            return False
        return date.today() > self.fecha_vencimiento
