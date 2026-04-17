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


class IsDirectorOrAbove(BasePermission):
    """Permite acceso a SUPERADMIN, ADMIN_JARDIN y DIRECTOR."""

    ALLOWED_ROLES = {"SUPERADMIN", "ADMIN_JARDIN", "DIRECTOR"}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in self.ALLOWED_ROLES
        )
