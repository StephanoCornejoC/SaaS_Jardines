from django.db import models


class DashboardMetric(models.Model):
    fecha = models.DateField(unique=True, verbose_name="Fecha")
    total_alumnos = models.IntegerField(default=0, verbose_name="Total alumnos")
    total_profesores = models.IntegerField(default=0, verbose_name="Total profesores")
    alumnos_por_nivel = models.JSONField(
        default=dict, verbose_name="Alumnos por nivel"
    )
    ingresos_mes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Ingresos del mes"
    )
    egresos_mes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Egresos del mes"
    )
    balance_mes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Balance del mes"
    )
    porcentaje_morosidad = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="% Morosidad"
    )
    porcentaje_asistencia = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="% Asistencia"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Métrica del dashboard"
        verbose_name_plural = "Métricas del dashboard"

    def __str__(self):
        return f"Métricas {self.fecha}"
