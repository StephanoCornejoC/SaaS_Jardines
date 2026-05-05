from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models


class Plan(models.Model):
    """Plan del SaaS. Hay un plan principal vigente y se pueden crear planes
    promocionales / de campaña en paralelo."""

    nombre = models.CharField(max_length=80, default="Plan COREM")
    precio_mensual = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("120.00"),
        help_text="Precio mensual por jardín en soles",
    )
    es_promocional = models.BooleanField(
        default=False,
        verbose_name="Promocional / campaña",
        help_text="Marca si es un plan promocional o de campaña (no el plan principal)",
    )
    descripcion = models.CharField(
        max_length=240,
        blank=True,
        help_text="Descripción visible (ej: '2x1 mes de aniversario', 'Verano 2026', etc.)",
    )
    activo = models.BooleanField(default=True)
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ("es_promocional", "-activo", "-creado_at")

    def __str__(self):
        if self.es_promocional:
            return f"{self.nombre} (promo · S/ {self.precio_mensual})"
        return f"{self.nombre} (S/ {self.precio_mensual}/mes)"

    @classmethod
    def vigente(cls):
        """Plan principal vigente (no promocional)."""
        return (
            cls.objects.filter(activo=True, es_promocional=False)
            .order_by("-creado_at")
            .first()
        )


class TenantSubscription(models.Model):
    """Suscripción de un jardín al SaaS."""

    class Estado(models.TextChoices):
        TRIAL = "TRIAL", "Prueba"
        ACTIVA = "ACTIVA", "Activa"
        MOROSA = "MOROSA", "Mora"
        BLOQUEADA = "BLOQUEADA", "Bloqueada"
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
    fecha_alta = models.DateField(
        default=date.today,
        verbose_name="Fecha de alta",
        help_text="Fecha en que el jardín fue dado de alta en COREM (inicio del periodo de prueba).",
    )
    trial_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Trial hasta",
        help_text="Hasta esta fecha el jardín no se cobra. Default: alta + 30 días.",
    )
    dia_cobro = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Día de cobro",
        help_text="Día del mes en que se emite el cobro (1-28).",
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

    @property
    def proximo_cobro(self):
        """Fecha estimada del próximo cobro mensual.
        - Si aún está en trial: el día siguiente al fin del trial.
        - Si ya pasó el trial: el próximo `dia_cobro` del calendario.
        """
        hoy = date.today()
        # Aún en trial
        if self.trial_hasta and hoy <= self.trial_hasta:
            return self.trial_hasta + timedelta(days=1)
        # Pasado el trial: buscar el siguiente día de cobro
        dia = max(1, min(28, self.dia_cobro or 1))
        candidato = date(hoy.year, hoy.month, dia)
        if candidato <= hoy:
            mes = hoy.month + 1
            anio = hoy.year
            if mes > 12:
                mes = 1
                anio += 1
            candidato = date(anio, mes, dia)
        return candidato

    def save(self, *args, **kwargs):
        if not self.trial_hasta:
            self.trial_hasta = self.fecha_alta + timedelta(days=30)
        if not self.precio_acordado and self.plan_id:
            self.precio_acordado = self.plan.precio_mensual
        # Clamp dia_cobro a 1-28 (evitamos meses cortos)
        if self.dia_cobro:
            self.dia_cobro = max(1, min(28, int(self.dia_cobro)))
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
        help_text="Si el gasto aplica a un jardín específico",
    )
    notas = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gasto operativo"
        verbose_name_plural = "Gastos operativos"
        ordering = ("-fecha",)

    def __str__(self):
        return f"{self.concepto} — S/ {self.monto} ({self.fecha})"
