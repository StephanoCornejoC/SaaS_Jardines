"""
Permission classes de DRF basadas en el campo `User.role`.

Roles del SaaS:
- SUPERADMIN: solo accede al admin Django de la plataforma (panel COREM).
  En las APIs del tenant es equivalente a ADMIN_JARDIN por compatibilidad.
- ADMIN_JARDIN (directora): acceso completo a las APIs de su jardín.
- TEACHER (profesor/a): acceso limitado a asistencia (full) + lectura
  de aulas y alumnos (sin datos sensibles como apoderados o ficha médica).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _user_role(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "role", None)


class IsSuperadmin(BasePermission):
    """Permite acceso solo a usuarios con rol SUPERADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin
        )


class IsAdminJardinOrAbove(BasePermission):
    """Permite acceso a SUPERADMIN y ADMIN_JARDIN. Bloquea TEACHER."""

    ALLOWED_ROLES = {"SUPERADMIN", "ADMIN_JARDIN"}
    message = "Esta acción requiere rol de Administrador del jardín."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in self.ALLOWED_ROLES
        )


class IsTeacherOrAdmin(BasePermission):
    """
    Permite acceso a ADMIN_JARDIN, SUPERADMIN o TEACHER autenticado.

    Usar en viewsets que las profesoras necesitan para operar (típicamente
    asistencia). Las restricciones específicas de TEACHER (ej. solo
    registrar asistencia del día actual) se aplican dentro del propio
    viewset, no acá.
    """

    ALLOWED_ROLES = {"SUPERADMIN", "ADMIN_JARDIN", "TEACHER"}
    message = "Debe iniciar sesión para acceder."

    def has_permission(self, request, view):
        return _user_role(request.user) in self.ALLOWED_ROLES


class IsAdminJardinOrTeacherReadOnly(BasePermission):
    """
    ADMIN_JARDIN / SUPERADMIN: acceso completo (read + write).
    TEACHER: solo lectura (GET, HEAD, OPTIONS).

    Usar en viewsets que la profesora necesita leer para tomar asistencia
    (lista de aulas, lista de alumnos sin datos sensibles) pero no modificar.
    """

    message = "Los profesores solo pueden consultar este recurso."

    def has_permission(self, request, view):
        role = _user_role(request.user)
        if role in ("ADMIN_JARDIN", "SUPERADMIN"):
            return True
        if role == "TEACHER":
            return request.method in SAFE_METHODS
        return False


# IsDirectorOrAbove fue removida tras el cleanup #55: el rol DIRECTOR ya
# no existe en User.Role. Las views que necesiten "admin o más arriba"
# deben usar `IsAdminJardinOrAbove` directamente.
