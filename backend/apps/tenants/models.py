from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django_tenants.utils import schema_context


class Tenant(TenantMixin):
    """
    Modelo de Tenant (Jardín). Cada jardín opera en su propio schema PostgreSQL.

    Decisión arquitectónica:
    - Existen 4 planes (Mini / Plus / Pro / Max) escalonados por cantidad de
      alumnos activos del jardín. El plan aplicable se determina con
      `Plan.por_alumnos(tenant.alumnos_activos_count())`.
    - El plan se asigna manualmente vía `platform.TenantSubscription.plan`.
      No se cambia automáticamente cuando el jardín crece de tier: cuando
      el conteo de alumnos excede el rango del plan, el sistema genera una
      alerta para que soporte interno coordine el upgrade con la directora
      (decisión humana, no automática).
    - El precio efectivamente cobrado se guarda en `precio_acordado` de la
      suscripción y puede ser distinto al `precio_mensual` del plan
      (soporta negociación caso por caso, sin bajar de `precio_minimo`).
    """

    nombre = models.CharField("Nombre del jardín", max_length=255)
    ruc = models.CharField("RUC", max_length=11, unique=True)
    direccion = models.TextField("Dirección", blank=True, default="")
    telefono = models.CharField("Teléfono", max_length=20, blank=True, default="")
    email = models.EmailField("Correo electrónico", blank=True, default="")
    logo = models.ImageField("Logo", upload_to="tenants/logos/", null=True, blank=True)
    activo = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    # django_tenants requires auto_create_schema
    auto_create_schema = True

    class Meta:
        verbose_name = "Jardín"
        verbose_name_plural = "Jardines"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.schema_name})"

    def alumnos_activos_count(self) -> int:
        """
        Cantidad de alumnos con estado=ACTIVO en el schema de este jardín.

        OJO: esta operación cambia de schema (Postgres SET search_path) para
        consultar la tabla `students_student` del tenant. Es relativamente
        cara — evitar llamarla en loops sin caché. Si el schema todavía no
        está creado o no tiene la tabla, devuelve 0.
        """
        from django.db import connection

        if not self.schema_name or self.schema_name == "public":
            return 0
        try:
            with schema_context(self.schema_name):
                # Import dentro del schema_context para que el ORM resuelva
                # la tabla en el schema correcto.
                from apps.students.models import Student
                return Student.objects.filter(estado=Student.Estado.ACTIVO).count()
        except Exception:
            # Schema sin migraciones aún, o cualquier error de conexión:
            # devolvemos 0 en vez de explotar el admin.
            return 0
        finally:
            # Asegurar que volvemos al schema público para no contaminar la
            # request actual del SUPERADMIN.
            connection.set_schema_to_public()

    def tier_correcto(self):
        """
        Plan que corresponde según el conteo actual de alumnos activos.

        Lazy-importa Plan para evitar import circular
        (platform.models importa tenants vía FK string).
        """
        from apps.platform.models import Plan
        return Plan.por_alumnos(self.alumnos_activos_count())


class Domain(DomainMixin):
    """
    Dominio asociado a un Tenant. django_tenants usa esto para resolver el tenant.
    """

    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"

    def __str__(self):
        return self.domain
