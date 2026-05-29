from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class Plan(models.Model):
    """
    Planes del SaaS escalonados por cantidad de alumnos del jardín.

    DECISIÓN ESTRATÉGICA (28-may-2026):
    Todos los planes (Mini / Plus / Pro / Max) entregan EXACTAMENTE las
    mismas funcionalidades del SaaS. La diferencia entre tiers es solo el
    rango de alumnos y el precio. No hay gating de módulos por plan.

    Esto contradice el roadmap previo de features diferenciadas — esa
    decisión quedó obsoleta. Razones del cambio:
    - El producto completo desde día 1 es mejor gancho comercial
    - Cero gating en código (sin lógica "este plan puede / no puede")
    - La directora no piensa "qué pierdo" sino "qué obtengo por el precio"

    El precio público (`precio_mensual`) y el piso negociable (`precio_minimo`)
    definen un rango: el `precio_acordado` de cada TenantSubscription puede
    ser CUALQUIER valor entre ambos, no solo los extremos. Negociación caso
    por caso por parte de soporte/ventas.
    """

    SLUG_MINI = "mini"
    SLUG_PLUS = "plus"
    SLUG_PRO = "pro"
    SLUG_MAX = "max"

    nombre = models.CharField(max_length=80)
    slug = models.SlugField(
        max_length=20,
        unique=True,
        help_text="Identificador único en código (mini, plus, pro, max).",
    )
    alumnos_min = models.PositiveSmallIntegerField(
        default=0,
        help_text="Cantidad mínima de alumnos activos para que aplique este plan.",
    )
    alumnos_max = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Cantidad máxima de alumnos activos. Dejar vacío significa sin límite.",
    )
    precio_mensual = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Precio público del plan en soles. Es el precio que se muestra en marketing.",
    )
    precio_minimo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Piso negociable. Soporte interno NO debe cerrar ventas por debajo de este monto.",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está desactivado, no se asigna a jardines nuevos. Los jardines existentes lo conservan.",
    )
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ("alumnos_min",)

    def __str__(self):
        return f"{self.nombre} (S/ {self.precio_mensual}/mes)"

    @property
    def rango_alumnos_texto(self):
        if self.alumnos_max is None:
            return f"{self.alumnos_min}+ alumnos"
        return f"{self.alumnos_min}–{self.alumnos_max} alumnos"

    def cubre(self, n_alumnos: int) -> bool:
        """¿Este plan aplica a un jardín con n_alumnos activos?"""
        if n_alumnos < self.alumnos_min:
            return False
        if self.alumnos_max is not None and n_alumnos > self.alumnos_max:
            return False
        return True

    @classmethod
    def por_alumnos(cls, n_alumnos: int):
        """
        Retorna el Plan activo que corresponde a `n_alumnos` activos.

        Sustituye al antiguo `Plan.vigente()` (que devolvía un único plan
        global). Ahora la respuesta depende del tamaño del jardín.

        Si no encuentra match (ej. n_alumnos=0 y el tier Mini empieza en 1),
        devuelve el plan con `alumnos_min` más bajo entre los activos.
        """
        n = max(0, int(n_alumnos))
        qs = cls.objects.filter(activo=True).order_by("alumnos_min")
        for plan in qs:
            if plan.cubre(n):
                return plan
        return qs.first()


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
        help_text=(
            "Precio negociado para este jardín. Puede ser CUALQUIER valor "
            "entre el precio_minimo y el precio_mensual del plan asignado. "
            "Default al crearse: precio_mensual del plan."
        ),
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

    def clean(self):
        """Valida que el precio_acordado esté dentro del rango del plan.

        Permite cualquier valor entre `plan.precio_minimo` y
        `plan.precio_mensual` (ambos inclusive). Soporte que intente cerrar
        ventas por debajo del piso ve un error de validación en el admin.
        """
        from django.core.exceptions import ValidationError
        super().clean()
        if self.plan_id and self.precio_acordado is not None:
            piso = self.plan.precio_minimo
            techo = self.plan.precio_mensual
            if self.precio_acordado < piso:
                raise ValidationError({
                    "precio_acordado": (
                        f"El precio acordado (S/{self.precio_acordado}) está por "
                        f"debajo del piso negociable del plan {self.plan.nombre} "
                        f"(S/{piso}). Para casos especiales, modificar el "
                        f"precio_minimo del plan o crear un acuerdo explícito."
                    ),
                })
            if self.precio_acordado > techo:
                raise ValidationError({
                    "precio_acordado": (
                        f"El precio acordado (S/{self.precio_acordado}) supera "
                        f"el precio público del plan {self.plan.nombre} "
                        f"(S/{techo}). ¿Quisiste asignar otro plan?"
                    ),
                })

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


class PlatformAlert(models.Model):
    """
    Alertas operativas del SaaS visibles solo para el SUPERADMIN.

    Las alertas NO son user-facing — sirven para que soporte interno detecte
    situaciones que requieren acción humana (ej. un jardín que creció de tier
    y hay que coordinar el upgrade con la directora por WhatsApp).

    Idempotencia: solo puede existir una alerta abierta (sin resolver) por
    cada par (tenant, tipo). El cron diario actualiza la existente en lugar
    de crear duplicados. Cuando soporte resuelve la alerta, se marca con
    `resuelta_at` y la próxima detección crea una nueva si vuelve a aplicar.
    """

    class Tipo(models.TextChoices):
        TIER_MISMATCH = "TIER_MISMATCH", "Tier desactualizado"
        # Reservar slots para alertas futuras:
        # MORA_PROLONGADA = "MORA_PROLONGADA", "Mora prolongada"
        # SIN_ACTIVIDAD   = "SIN_ACTIVIDAD",   "Sin actividad"

    class Nivel(models.TextChoices):
        INFO = "INFO", "Informativo"
        WARNING = "WARNING", "Advertencia"
        CRITICAL = "CRITICAL", "Crítico"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="alertas",
        verbose_name="Jardín",
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    nivel = models.CharField(max_length=10, choices=Nivel.choices, default=Nivel.INFO)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    contexto = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Datos estructurados de la alerta. Para TIER_MISMATCH: "
            "{plan_actual, tier_correcto, alumnos_activos}."
        ),
    )
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)
    resuelta_at = models.DateTimeField(null=True, blank=True)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_resueltas",
    )
    notas_resolucion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Alerta del SaaS"
        verbose_name_plural = "Alertas del SaaS"
        ordering = ("-creado_at",)
        constraints = [
            # Solo una alerta abierta (sin resolver) por par (tenant, tipo).
            # Cuando se resuelve (resuelta_at no nulo) puede existir otra
            # del mismo tipo para el mismo tenant.
            models.UniqueConstraint(
                fields=("tenant", "tipo"),
                condition=Q(resuelta_at__isnull=True),
                name="unique_open_alert_per_tenant_type",
            ),
        ]

    def __str__(self):
        estado = "ABIERTA" if self.resuelta_at is None else "RESUELTA"
        return f"[{estado}] {self.get_tipo_display()} · {self.tenant.nombre}"

    @property
    def esta_resuelta(self) -> bool:
        return self.resuelta_at is not None
