from django.conf import settings
from django.db import models


class Communication(models.Model):
    class Tipo(models.TextChoices):
        GENERAL = "GENERAL", "General"
        POR_AULA = "POR_AULA", "Por aula"

    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(verbose_name="Contenido")
    tipo = models.CharField(
        max_length=10, choices=Tipo.choices, verbose_name="Tipo"
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name="Aula",
        help_text="Solo requerido si el tipo es POR_AULA",
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications_sent",
        verbose_name="Enviado por",
    )
    fecha_envio = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de envío"
    )
    enviado = models.BooleanField(default=False, verbose_name="Enviado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comunicación"
        verbose_name_plural = "Comunicaciones"

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"
