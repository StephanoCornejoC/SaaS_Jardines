from django.db import models


class Classroom(models.Model):
    class NivelEdad(models.IntegerChoices):
        DOS = 2, "2 años"
        TRES = 3, "3 años"
        CUATRO = 4, "4 años"
        CINCO = 5, "5 años"

    nombre = models.CharField(max_length=100, verbose_name="Nombre", unique=True)
    nivel_edad = models.IntegerField(
        choices=NivelEdad.choices, verbose_name="Nivel de edad"
    )
    capacidad = models.PositiveIntegerField(default=25, verbose_name="Capacidad")
    profesor_titular = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aulas_titular",
        verbose_name="Profesor titular",
    )
    profesor_auxiliar = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aulas_auxiliar",
        verbose_name="Profesor auxiliar",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nivel_edad", "nombre"]
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"

    def __str__(self):
        return f"{self.nombre} ({self.nivel_edad} años)"

    @property
    def alumnos_count(self):
        return self.students.count()

    @property
    def disponible(self):
        return self.alumnos_count < self.capacidad
