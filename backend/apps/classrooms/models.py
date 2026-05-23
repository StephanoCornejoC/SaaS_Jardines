from django.core.exceptions import ValidationError
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
    # `limit_choices_to` filtra el queryset del admin/ModelForm para que solo
    # aparezcan profesores del tipo correcto. La validación dura sigue en
    # `clean()` por si alguien fuerza el FK por API o ORM.
    profesor_titular = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aulas_titular",
        verbose_name="Profesor titular",
        limit_choices_to={"tipo": "TITULAR"},
    )
    profesor_auxiliar = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aulas_auxiliar",
        verbose_name="Profesor auxiliar",
        limit_choices_to={"tipo": "AUXILIAR"},
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

    def clean(self):
        """Validaciones a nivel modelo (corre en admin y full_clean explícito).

        - profesor_titular debe ser de tipo TITULAR.
        - profesor_auxiliar debe ser de tipo AUXILIAR.
        - No pueden ser el mismo profesor.
        """
        super().clean()
        errors = {}
        if self.profesor_titular_id and self.profesor_titular.tipo != "TITULAR":
            errors["profesor_titular"] = (
                "El profesor titular debe ser de tipo TITULAR. "
                f"'{self.profesor_titular}' es {self.profesor_titular.get_tipo_display()}."
            )
        if self.profesor_auxiliar_id and self.profesor_auxiliar.tipo != "AUXILIAR":
            errors["profesor_auxiliar"] = (
                "El profesor auxiliar debe ser de tipo AUXILIAR. "
                f"'{self.profesor_auxiliar}' es {self.profesor_auxiliar.get_tipo_display()}."
            )
        if (
            self.profesor_titular_id
            and self.profesor_auxiliar_id
            and self.profesor_titular_id == self.profesor_auxiliar_id
        ):
            errors["profesor_auxiliar"] = (
                "El profesor titular y el auxiliar no pueden ser la misma persona."
            )
        if errors:
            raise ValidationError(errors)
