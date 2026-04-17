from django.conf import settings
from django.db import models


class Attendance(models.Model):
    class Estado(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        AUSENTE = "AUSENTE", "Ausente"
        TARDANZA = "TARDANZA", "Tardanza"
        JUSTIFICADO = "JUSTIFICADO", "Justificado"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Alumno",
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.PROTECT,
        related_name="attendances",
        verbose_name="Aula",
    )
    fecha = models.DateField(verbose_name="Fecha")
    estado = models.CharField(
        max_length=12, choices=Estado.choices, verbose_name="Estado"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendances_registered",
        verbose_name="Registrado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "fecha")
        ordering = ["-fecha", "student__apellidos"]
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"

    def __str__(self):
        return f"{self.student} - {self.fecha} ({self.get_estado_display()})"
