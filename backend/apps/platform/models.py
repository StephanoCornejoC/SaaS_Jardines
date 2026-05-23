from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models


class Plan(models.Model):
    """Único plan del SaaS. Se mantiene como modelo para tener histórico
    de cambios de precio. Solo debería existir 1 fila marcada como activa."""

    nombre = models.CharField(max_length=80, default="Plan COREM")
    precio_mensual = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("120.00"),
        help_text="Precio mensual por jardín en soles",
    )
    activo = models.BooleanField(default=True)
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plan / Configuración"
        ordering = ("-activo", "-creado_at")

    def __str__(self):
        return f"{self.nombre} (S/ {self.precio_mensual}/mes)"

    @classmethod
    def vigente(cls):
        return cls.objects.filter(activo=True).order_by("-creado_at").first()


class TenantSubscription(models.Model):
    """Suscripción de un jardín al SaaS."""

    class Estado(models.TextChoices):
        TRIAL = "TRIAL", "En periodo de prueba"
        ACTIVA = "ACTIVA", "Activa"
        MOROSA = "MOROSA", "En mora (3-7 días)"
        BLOQUEADA = "BLOQUEADA", "Bloqueada por impago"
        CANCELADA = "CANCELADA", "Cancelada"

    tenant = models.OneToOneField(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="suscripcion",
        verbose_name="Jardín",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="suscripciones",
    )
    precio_acordado = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Precio negociado para este jardín. Default = precio del plan.",
    )
    fecha_alta = models.DateField(default=date.today)
    trial_hasta = models.DateField(
        null=True,
        blank=True,
        help_text="Hasta esta fecha el jardín no se cobra. Default: alta + 1 mes.",
    )
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.TRIAL
    )
    notas = models.TextField(blank=True)

    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ("-fecha_alta",)

    def __str__(self):
        return f"{self.tenant} — {self.get_estado_display()}"

    def en_trial(self):
        return self.trial_hasta and date.today() <= self.trial_hasta

    def save(self, *args, **kwargs):
        if not self.trial_hasta:
            self.trial_hasta = self.fecha_alta + timedelta(days=30)
        if not self.precio_acordado and self.plan_id:
            self.precio_acordado = self.plan.precio_mensual
        super().save(*args, **kwargs)


class PlatformInvoice(models.Model):
    """Cobro mensual del SaaS a cada jardín."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADA = "PAGADA", "Pagada"
        VENCIDA = "VENCIDA", "Vencida"
        CONDONADA = "CONDONADA", "Condonada"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name="Jardín",
    )
    mes = models.PositiveSmallIntegerField()
    anio = models.PositiveSmallIntegerField()
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_emision = models.DateField(default=date.today)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(
        max_length=20, blank=True, help_text="Yape, Plin, Transferencia, etc."
    )
    referencia = models.CharField(max_length=80, blank=True, help_text="Nº de operación")
    notas = models.TextField(blank=True)

    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cobro mensual"
        verbose_name_plural = "Cobros mensuales"
        ordering = ("-anio", "-mes", "tenant__nombre")
        unique_together = ("tenant", "mes", "anio")

    def __str__(self):
        return f"{self.tenant} — {self.mes:02d}/{self.anio} — S/ {self.monto}"

    @property
    def dias_vencida(self):
        if self.estado == self.Estado.PAGADA or not self.fecha_vencimiento:
            return 0
        delta = (date.today() - self.fecha_vencimiento).days
        return max(0, delta)


class PlatformCost(models.Model):
    """Gasto operativo del SaaS."""

    class Categoria(models.TextChoices):
        HOSTING_BACK = "HOSTING_BACK", "Hosting backend (Railway)"
        HOSTING_FRONT = "HOSTING_FRONT", "Hosting frontend (Vercel)"
        DOMINIO = "DOMINIO", "Dominio"
        EMAIL = "EMAIL", "Email / SMTP"
        STORAGE = "STORAGE", "Almacenamiento"
        OTROS = "OTROS", "Otros"

    concepto = models.CharField(max_length=160)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(default=date.today)
    recurrente = models.BooleanField(
        default=False, help_text="Marca si es un gasto mensual recurrente"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="costs",
        help_text=(
            "Si el gasto aplica a un jardín específico, asignarlo. "
            "Si es un gasto genérico del SaaS (Railway, dominio, etc.), "
            "dejarlo vacío."
        ),
    )
    notas = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Costo del SaaS"
        verbose_name_plural = "Costos del SaaS"
        ordering = ("-fecha",)

    def __str__(self):
        return f"{self.concepto} — S/ {self.monto} ({self.fecha})"
