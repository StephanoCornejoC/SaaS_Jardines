from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Teacher(models.Model):
    class Tipo(models.TextChoices):
        TITULAR = "TITULAR", "Titular"
        AUXILIAR = "AUXILIAR", "Auxiliar"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_profile",
        verbose_name="Usuario",
    )
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.TITULAR,
        verbose_name="Tipo de profesor",
        help_text=(
            "Titular: a cargo del aula. Auxiliar: apoya al titular. "
            "Solo los Titulares pueden asignarse como profesor_titular "
            "del aula; solo los Auxiliares como profesor_auxiliar."
        ),
    )
    especialidad = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    fecha_ingreso = models.DateField(verbose_name="Fecha de ingreso")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()


class TeacherContract(models.Model):
    class TipoContrato(models.TextChoices):
        TIEMPO_COMPLETO = "TIEMPO_COMPLETO", "Tiempo completo"
        MEDIO_TIEMPO = "MEDIO_TIEMPO", "Medio tiempo"
        POR_HORAS = "POR_HORAS", "Por horas"

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name="Profesor",
    )
    tipo = models.CharField(
        max_length=20, choices=TipoContrato.choices, verbose_name="Tipo de contrato"
    )
    sueldo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sueldo")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin",
        help_text="Dejar vacío para contrato indefinido",
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return f"{self.teacher} - {self.get_tipo_display()} ({self.fecha_inicio})"


class TeacherPayment(models.Model):
    class MetodoPago(models.TextChoices):
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        EFECTIVO = "EFECTIVO", "Efectivo"
        DEPOSITO = "DEPOSITO", "Depósito"

    contract = models.ForeignKey(
        TeacherContract,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Contrato",
    )
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Mes",
    )
    anio = models.IntegerField(verbose_name="Año")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    fecha_pago = models.DateField(verbose_name="Fecha de pago")
    metodo_pago = models.CharField(
        max_length=15, choices=MetodoPago.choices, verbose_name="Método de pago"
    )
    comprobante = models.CharField(max_length=200, blank=True, verbose_name="Comprobante")
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("contract", "mes", "anio")
        ordering = ["-anio", "-mes"]
        verbose_name = "Sueldo pagado"
        verbose_name_plural = "Sueldos"

    def __str__(self):
        return f"Pago {self.mes}/{self.anio} - {self.contract.teacher}"
