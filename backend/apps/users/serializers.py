from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer de lectura para usuarios."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "telefono", "is_active")
        read_only_fields = ("id",)


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de usuarios."""

    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "role", "telefono")

    def validate_role(self, value):
        request = self.context.get("request")
        if request and request.user:
            user_role = request.user.role
            role_hierarchy = [
                "PROFESOR",
                "SECRETARIA",
                "DIRECTOR",
                "ADMIN_JARDIN",
                "SUPERADMIN",
            ]
            if user_role in role_hierarchy and value in role_hierarchy:
                if role_hierarchy.index(value) > role_hierarchy.index(user_role):
                    raise serializers.ValidationError(
                        "No puede asignar un rol superior al suyo."
                    )
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer para login personalizado."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()

        # SECURITY [VULN-018]: Invalidate all existing JWT tokens so that
        # sessions using the old password are forced to re-authenticate.
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        return user
