import uuid

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsAdminJardinOrAbove
from .serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de usuarios.
    - list / retrieve: cualquier usuario autenticado.
    - create / update / destroy: solo SUPERADMIN o ADMIN_JARDIN.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['SUPERADMIN', 'ADMIN_JARDIN']:
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminJardinOrAbove()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {"detail": "No puede eliminarse a si mismo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Retorna el perfil del usuario autenticado."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """Endpoint para que el usuario autenticado cambie su contraseña."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """Cierra la sesión del usuario.

        Rota `active_session_id` → el access token vigente queda inválido en
        el próximo request (su claim 'sid' deja de coincidir), así un token
        robado deja de servir de inmediato sin esperar a que expire. Si se
        manda el refresh en el body, también se blacklistea.
        """
        user = request.user
        user.active_session_id = uuid.uuid4()
        user.save(update_fields=["active_session_id"])

        refresh = request.data.get("refresh")
        if refresh:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                RefreshToken(refresh).blacklist()
            except Exception:
                # Token inválido/expirado: la rotación de sid ya cerró la sesión.
                pass

        return Response({"detail": "Sesión cerrada."}, status=status.HTTP_200_OK)
