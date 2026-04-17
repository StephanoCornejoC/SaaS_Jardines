from django.db import models


class TimestampMixin(models.Model):
    """Mixin abstracto que agrega campos created_at y updated_at."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        abstract = True


class TenantFilterMixin:
    """
    Mixin para ViewSets que asegura el filtrado por tenant actual.
    Defensa en profundidad: aunque django-tenants maneja el aislamiento
    por schema, este mixin agrega una capa extra de seguridad filtrando
    el queryset por la conexión/tenant activo.
    """

    def get_queryset(self):
        queryset = super().get_queryset()

        # django-tenants ya filtra por schema, pero si el modelo
        # tiene un campo tenant/school explícito, filtrar aquí también.
        if hasattr(queryset.model, "tenant"):
            from django.db import connection

            current_tenant = getattr(connection, "tenant", None)
            if current_tenant:
                queryset = queryset.filter(tenant=current_tenant)

        return queryset
