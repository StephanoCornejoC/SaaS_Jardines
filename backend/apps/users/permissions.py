from rest_framework.permissions import BasePermission


class IsSuperadmin(BasePermission):
    """Permite acceso solo a usuarios con rol SUPERADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin
        )


class IsAdminJardinOrAbove(BasePermission):
    """Permite acceso a SUPERADMIN y ADMIN_JARDIN."""

    ALLOWED_ROLES = {"SUPERADMIN", "ADMIN_JARDIN"}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in self.ALLOWED_ROLES
        )


# IsDirectorOrAbove fue removida tras el cleanup #55: el rol DIRECTOR ya
# no existe en User.Role. Las views que necesiten "admin o más arriba"
# deben usar `IsAdminJardinOrAbove` directamente.
