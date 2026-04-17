from datetime import date

from django.db import models


class Student(models.Model):
    class Genero(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        RETIRADO = "RETIRADO", "Retirado"
        EGRESADO = "EGRESADO", "Egresado"
        ELIMINADO = "ELIMINADO", "Eliminado"

    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    genero = models.CharField(max_length=1, choices=Genero.choices, verbose_name="Género")
    foto = models.ImageField(upload_to="students/fotos/", null=True, blank=True)
    classroom = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Aula",
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_ingreso = models.DateField(verbose_name="Fecha de ingreso")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    @property
    def edad(self):
        today = date.today()
        born = self.fecha_nacimiento
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class Guardian(models.Model):
    class Parentesco(models.TextChoices):
        PADRE = "PADRE", "Padre"
        MADRE = "MADRE", "Madre"
        TUTOR = "TUTOR", "Tutor"
        OTRO = "OTRO", "Otro"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="apoderados",
        verbose_name="Alumno",
    )
    dni = models.CharField(max_length=8, verbose_name="DNI")
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    parentesco = models.CharField(max_length=10, choices=Parentesco.choices)
    es_principal = models.BooleanField(default=False, verbose_name="Es apoderado principal")

    class Meta:
        unique_together = ("student", "dni")
        verbose_name = "Apoderado"
        verbose_name_plural = "Apoderados"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.get_parentesco_display()})"


class MedicalRecord(models.Model):
    class TipoSangre(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="ficha_medica",
        verbose_name="Alumno",
    )
    tipo_sangre = models.CharField(
        max_length=3,
        choices=TipoSangre.choices,
        verbose_name="Tipo de sangre",
    )
    alergias = models.TextField(blank=True, verbose_name="Alergias")
    seguro = models.CharField(max_length=200, blank=True, verbose_name="Seguro médico")
    hospital_referencia = models.CharField(
        max_length=200, blank=True, verbose_name="Hospital de referencia"
    )
    contacto_emergencia_nombre = models.CharField(
        max_length=200, verbose_name="Contacto de emergencia (nombre)"
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=20, verbose_name="Contacto de emergencia (teléfono)"
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ficha médica"
        verbose_name_plural = "Fichas médicas"

    def __str__(self):
        return f"Ficha médica de {self.student}"
