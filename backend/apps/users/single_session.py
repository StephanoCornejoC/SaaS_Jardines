"""
Single-session enforcement para JWT.

Política del producto comercial SAAS COREM:
  - Solo se permite UNA sesión activa por usuario.
  - Si el usuario hace login desde otro navegador/dispositivo,
    la sesión anterior queda invalidada inmediatamente (forzar logout remoto).

Implementación:
  - User.active_session_id: UUID que se regenera en cada login.
  - El JWT incluye ese UUID como claim "sid".
  - En cada request, JWTSingleSessionAuthentication verifica que el "sid"
    del token coincida con el active_session_id del usuario.
  - Si no coincide -> 401 AuthenticationFailed ("Sesión cerrada por nuevo inicio").
"""

import uuid

from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

SESSION_CLAIM = "sid"


class SingleSessionTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Al hacer login, regenera el active_session_id del usuario
    y lo embebe en el JWT (claim "sid"). Cualquier sesión anterior
    con un UUID distinto queda inmediatamente invalidada.
    """

    @classmethod
    def get_token(cls, user):
        # Regenerar el identificador de sesión -> invalida sesiones previas
        new_sid = uuid.uuid4()
        user.active_session_id = new_sid
        user.save(update_fields=["active_session_id"])

        token = super().get_token(user)
        token[SESSION_CLAIM] = str(new_sid)
        return token


class SingleSessionRefreshMixin:
    """
    Al hacer refresh de token, preservamos el mismo sid para no romper
    la sesión en curso. El sid del refresh debe coincidir con el activo
    del usuario; si no coincide, rechazamos (la sesión fue superseded).
    """

    def validate(self, attrs):
        # Parseamos el refresh ANTES de super().validate() para verificar sid
        refresh = RefreshToken(attrs["refresh"])
        sid = refresh.get(SESSION_CLAIM)

        if sid is None:
            # Refresh antiguo sin sid -> no aceptar
            from rest_framework import exceptions
            raise exceptions.AuthenticationFailed(
                "Refresh token sin identificador de sesión. Vuelva a iniciar sesión.",
                code="session_claim_missing",
            )

        # Verificamos que el sid siga siendo el activo del usuario
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_id = refresh.get("user_id")
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            from rest_framework import exceptions
            raise exceptions.AuthenticationFailed("Usuario no existe.")

        if str(user.active_session_id) != str(sid):
            from rest_framework import exceptions
            raise exceptions.AuthenticationFailed(
                "Sesión superseded por nuevo login. Vuelva a iniciar sesión.",
                code="session_superseded",
            )

        # Delegamos al validador estándar (genera nuevo access)
        data = super().validate(attrs)

        # Inyectamos sid en el nuevo access token decodificándolo y re-encodándolo
        from rest_framework_simplejwt.tokens import AccessToken
        new_access = AccessToken(data["access"])
        new_access[SESSION_CLAIM] = sid
        data["access"] = str(new_access)

        return data


class JWTSingleSessionAuthentication(JWTAuthentication):
    """
    Extiende la autenticación JWT estándar para verificar que
    el 'sid' del token coincida con User.active_session_id.

    Si el usuario ha hecho login en otro lado después de emitido este token,
    su active_session_id será diferente -> este token queda inválido.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        token_sid = validated_token.get(SESSION_CLAIM)
        if token_sid is None:
            # Tokens antiguos sin "sid" -> forzar re-login
            raise exceptions.AuthenticationFailed(
                "Token sin identificador de sesión. Vuelva a iniciar sesión.",
                code="session_claim_missing",
            )

        if str(user.active_session_id) != str(token_sid):
            raise exceptions.AuthenticationFailed(
                "Sesión cerrada porque se inició sesión desde otro dispositivo.",
                code="session_superseded",
            )

        return user
