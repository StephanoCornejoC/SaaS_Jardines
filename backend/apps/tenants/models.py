from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """
    Modelo de Tenant (Jardín). Cada jardín opera en su propio schema PostgreSQL.
    """

    class Plan(models.TextChoices):
        BASICO = "BASICO", "Básico"
        PROFESIONAL = "PROFESIONAL", "Profesional"
        PREMIUM = "PREMIUM", "Premium"

    nombre = models.CharField("Nombre del jardín", max_length=255)
    ruc = models.CharField("RUC", max_length=11, unique=True)
    direccion = models.TextField("Dirección", blank=True, default="")
    telefono = models.CharField("Teléfono", max_length=20, blank=True, default="")
    email = models.EmailField("Correo electrónico", blank=True, default="")
    logo = models.ImageField("Logo", upload_to="tenants/logos/", null=True, blank=True)
    plan = models.CharField(
        "Plan",
        max_length=20,
        choices=Plan.choices,
        default=Plan.BASICO,
    )
    activo = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    # django_tenants requires auto_create_schema
    auto_create_schema = True

    class Meta:
        verbose_name = "Jardín (Tenant)"
        verbose_name_plural = "Jardines (Tenants)"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.schema_name})"


class Domain(DomainMixin):
    """
    Dominio asociado a un Tenant. django_tenants usa esto para resolver el tenant.
    """

    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"

    def __str__(self):
        return self.domain
