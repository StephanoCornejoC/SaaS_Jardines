from django.db import models


class EmailLog(models.Model):
    class Tipo(models.TextChoices):
        RECORDATORIO_PAGO = "RECORDATORIO_PAGO", "Recordatorio de pago"
        COMUNICACION = "COMUNICACION", "Comunicación"
        ALERTA_ASISTENCIA = "ALERTA_ASISTENCIA", "Alerta de asistencia"
        BIENVENIDA = "BIENVENIDA", "Bienvenida"

    destinatario = models.EmailField(verbose_name="Destinatario")
    asunto = models.CharField(max_length=300, verbose_name="Asunto")
    contenido = models.TextField(verbose_name="Contenido")
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, verbose_name="Tipo"
    )
    enviado = models.BooleanField(default=False, verbose_name="Enviado")
    error = models.TextField(blank=True, verbose_name="Error")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log de email"
        verbose_name_plural = "Logs de email"

    def __str__(self):
        status = "OK" if self.enviado else "ERROR"
        return f"[{status}] {self.asunto} -> {self.destinatario}"
