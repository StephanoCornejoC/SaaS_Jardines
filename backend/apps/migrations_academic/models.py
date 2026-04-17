from django.conf import settings
from django.db import models


class AcademicMigration(models.Model):
    class Status(models.TextChoices):
        PREVIEW = "PREVIEW", "Preview"
        EJECUTADO = "EJECUTADO", "Ejecutado"
        ROLLBACK = "ROLLBACK", "Rollback"

    anio_origen = models.IntegerField(verbose_name="Año origen")
    anio_destino = models.IntegerField(verbose_name="Año destino")
    ejecutado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_migrations",
        verbose_name="Ejecutado por",
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de ejecución")
    total_migrados = models.IntegerField(default=0, verbose_name="Total migrados")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PREVIEW
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Migración académica"
        verbose_name_plural = "Migraciones académicas"

    def __str__(self):
        return f"Migración {self.anio_origen} -> {self.anio_destino} ({self.get_status_display()})"


class MigrationDetail(models.Model):
    migration = models.ForeignKey(
        AcademicMigration,
        on_delete=models.CASCADE,
        related_name="details",
        verbose_name="Migración",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="migration_details",
        verbose_name="Alumno",
    )
    aula_origen = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_details_origen",
        verbose_name="Aula origen",
    )
    aula_destino = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_details_destino",
        verbose_name="Aula destino",
    )
    estado_anterior = models.CharField(max_length=20, verbose_name="Estado anterior")
    estado_nuevo = models.CharField(max_length=20, verbose_name="Estado nuevo")

    class Meta:
        verbose_name = "Detalle de migración"
        verbose_name_plural = "Detalles de migración"

    def __str__(self):
        return f"{self.student} - {self.estado_anterior} -> {self.estado_nuevo}"
