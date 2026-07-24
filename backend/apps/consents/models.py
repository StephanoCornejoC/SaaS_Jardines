"""
Consentimientos informados (Ley 29733 - Protección de Datos Personales, Perú).

Modelo legal del SaaS:
- El JARDÍN es el RESPONSABLE del tratamiento (dueño de la relación con los
  apoderados). Por eso estos modelos viven en el schema del tenant: cada
  jardín define su propia política y guarda sus propios registros, aislados.
- COREM es el ENCARGADO del tratamiento (procesa por cuenta del jardín).

Dos piezas:
- `ConsentDocument`: la cláusula/política VERSIONADA que el apoderado acepta.
- `Consent`: el registro PROBATORIO de que un apoderado otorgó (o revocó) su
  consentimiento por un alumno, sobre una versión concreta del documento.
  Es evidencia de cumplimiento — nunca se borra; una revocación es una fila
  nueva con `otorgado=False`.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class ConsentType(models.TextChoices):
    DATOS_PERSONALES = "DATOS_PERSONALES", "Tratamiento de datos personales del menor"
    DATOS_SALUD = "DATOS_SALUD", "Tratamiento de datos de salud (ficha médica)"
    IMAGEN = "IMAGEN", "Uso de imagen (fotografías y video)"
    COMUNICACIONES = "COMUNICACIONES", "Envío de comunicaciones al apoderado"


class ConsentDocument(models.Model):
    """
    Documento de consentimiento versionado. El texto legal lo redacta el
    jardín (idealmente con un template revisado por un abogado). Cuando el
    texto cambia de forma sustantiva, se crea una versión nueva y se pide
    re-consentir — no se edita la versión ya consentida (integridad de la
    evidencia).
    """

    tipo = models.CharField(max_length=20, choices=ConsentType.choices, verbose_name="Tipo")
    version = models.PositiveIntegerField(default=1, verbose_name="Versión")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(
        verbose_name="Contenido",
        help_text="Texto completo de la cláusula/política que el apoderado acepta.",
    )
    obligatorio = models.BooleanField(
        default=True,
        verbose_name="Obligatorio",
        help_text="Si el jardín no puede prestar el servicio sin este consentimiento.",
    )
    vigente_desde = models.DateField(default=timezone.now, verbose_name="Vigente desde")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento de consentimiento"
        verbose_name_plural = "Documentos de consentimiento"
        unique_together = ("tipo", "version")
        ordering = ["tipo", "-version"]

    def __str__(self):
        return f"{self.get_tipo_display()} v{self.version}"


class Consent(models.Model):
    """
    Registro probatorio de una decisión de consentimiento de un apoderado
    por un alumno, sobre una versión concreta de un documento.

    El estado ACTUAL (otorgado / revocado) de un alumno frente a un documento
    es el de su fila más reciente por `(student, documento)`. Las filas
    históricas se conservan como evidencia — no se borran ni se editan.
    """

    documento = models.ForeignKey(
        ConsentDocument,
        on_delete=models.PROTECT,
        related_name="registros",
        verbose_name="Documento",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="consentimientos",
        verbose_name="Alumno",
    )
    guardian = models.ForeignKey(
        "students.Guardian",
        on_delete=models.PROTECT,
        related_name="consentimientos",
        null=True,
        blank=True,
        verbose_name="Apoderado que consiente",
    )
    otorgado = models.BooleanField(default=True, verbose_name="Otorgado")
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha de la decisión")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP de origen")
    user_agent = models.CharField(max_length=300, blank=True, default="")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consentimientos_registrados",
        verbose_name="Registrado por",
    )
    notas = models.TextField(blank=True, default="", verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Consentimiento"
        verbose_name_plural = "Consentimientos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["student", "documento"]),
            models.Index(fields=["documento", "otorgado"]),
        ]

    def __str__(self):
        estado = "otorgó" if self.otorgado else "revocó"
        return f"{self.student} — {estado} {self.documento}"
