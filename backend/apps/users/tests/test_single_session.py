"""Tests for single-session enforcement."""

import pytest
from rest_framework.test import APIClient

from apps.users.factories import UserFactory
from apps.users.single_session import (
    SESSION_CLAIM,
    SingleSessionTokenObtainPairSerializer,
)

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestSingleSession:
    def test_login_generates_sid(self, tenant):
        """Al hacer login, el token contiene un claim 'sid' y el User.active_session_id se regenera."""
        user = UserFactory()
        original_sid = user.active_session_id

        token = SingleSessionTokenObtainPairSerializer.get_token(user)
        user.refresh_from_db()

        assert token[SESSION_CLAIM] is not None
        assert user.active_session_id != original_sid
        assert str(user.active_session_id) == token[SESSION_CLAIM]

    def test_second_login_invalidates_first_session(self, tenant):
        """Un segundo login genera nuevo sid que invalida el token del primero."""
        user = UserFactory()

        token1 = SingleSessionTokenObtainPairSerializer.get_token(user)
        sid1 = token1[SESSION_CLAIM]
        access1 = str(token1.access_token)

        # Segundo login
        token2 = SingleSessionTokenObtainPairSerializer.get_token(user)
        sid2 = token2[SESSION_CLAIM]

        assert sid1 != sid2

        # El token del primer login ya no funciona porque active_session_id cambió
        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access1}")
        response = client.get("/api/v1/students/")
        assert response.status_code == 401
        assert "sesión" in str(response.data).lower() or "session" in str(response.data).lower()

    def test_current_session_token_still_works(self, tenant):
        """El token del login actual sigue funcionando."""
        user = UserFactory(role="ADMIN_JARDIN")
        token = SingleSessionTokenObtainPairSerializer.get_token(user)
        access = str(token.access_token)

        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.get("/api/v1/students/")
        assert response.status_code == 200

    def test_login_endpoint_sets_session_and_returns_token(self, tenant):
        """POST /auth/token/ con credenciales válidas regenera el sid y devuelve el token."""
        user = UserFactory()
        user.set_password("MyTest1234")
        user.save()
        original_sid = user.active_session_id

        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        response = client.post(
            "/api/v1/auth/token/",
            {"email": user.email, "password": "MyTest1234"},
            format="json",
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

        user.refresh_from_db()
        assert user.active_session_id != original_sid
