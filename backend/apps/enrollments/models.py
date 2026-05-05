from django.conf import settings
from django.db import models


class Enrollment(models.Model):
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Alumno",
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
        verbose_name="Aula",
    )
    anio_escolar = models.IntegerField(verbose_name="Año escolar")
    costo_matricula = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Costo de matrícula"
    )
    fecha_matricula = models.DateField(auto_now_add=True, verbose_name="Fecha de matrícula")
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments_created",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "anio_escolar")
        ordering = ["-anio_escolar", "student__apellidos"]
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"

    def __str__(self):
        return f"{self.student} - {self.anio_escolar}"
