import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class User(AbstractUser):
    """
    Usuario personalizado. Usa email como campo de autenticación en lugar de username.
    El producto comercial solo permite un rol funcional (ADMIN_JARDIN). El
    SUPERADMIN existe únicamente para el panel de COREM y NO puede operar
    dentro de un tenant.
    """

    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        ADMIN_JARDIN = "ADMIN_JARDIN", "Admin Jardín"

    # Eliminar username, usar email como identificador
    username = None
    email = models.EmailField("Correo electrónico", unique=True)

    role = models.CharField(
        "Rol",
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN_JARDIN,
    )
    telefono = models.CharField("Teléfono", max_length=20, blank=True, null=True)

    # SESSION_ENFORCEMENT: solo una sesión activa por usuario.
    # Al hacer login se genera un nuevo UUID; los tokens con UUIDs anteriores
    # se consideran inválidos y fuerzan cierre de sesión remota.
    active_session_id = models.UUIDField(
        "ID de sesión activa",
        default=uuid.uuid4,
        help_text="UUID de la sesión actualmente activa. Al hacer login se regenera.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["email"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    # --------------- Role helpers ---------------

    @property
    def is_superadmin(self) -> bool:
        return self.role == self.Role.SUPERADMIN

    @property
    def is_admin_jardin(self) -> bool:
        return self.role == self.Role.ADMIN_JARDIN
