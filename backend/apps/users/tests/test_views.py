"""API / view tests for users app."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.users.factories import ProfesorFactory, UserFactory

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestTokenEndpoints:
    """Tests for JWT authentication endpoints."""

    def test_login_success(self, auth_client, admin_user):
        """Login via SimpleJWT token obtain pair endpoint."""
        from rest_framework.test import APIClient

        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        response = client.post(
            "/api/v1/auth/token/",
            {"email": admin_user.email, "password": "TestPass1234"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, tenant):
        from rest_framework.test import APIClient

        user = UserFactory()
        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        response = client.post(
            "/api/v1/auth/token/",
            {"email": user.email, "password": "WrongPassword"},
            format="json",
        )
        assert response.status_code == 401

    def test_token_refresh(self, auth_client, admin_user):
        from rest_framework.test import APIClient

        from apps.users.single_session import SingleSessionTokenObtainPairSerializer

        client = APIClient()
        client.defaults["HTTP_HOST"] = "test.localhost"
        # Usar el serializer con sesión única para que el refresh traiga el claim sid
        refresh = SingleSessionTokenObtainPairSerializer.get_token(admin_user)
        response = client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data


class TestUserViewSet:
    """Tests for the UserViewSet CRUD operations."""

    def test_list_users_as_admin(self, auth_client, admin_user):
        # Create a few extra users
        UserFactory()
        UserFactory()
        client = auth_client(admin_user)
        response = client.get("/api/v1/auth/users/")
        assert response.status_code == 200
        # Admin sees all users (admin + 2 extras = 3)
        assert response.data["count"] >= 3

    def test_list_users_as_profesor_sees_only_self(self, auth_client, profesor_user):
        UserFactory()  # another user
        client = auth_client(profesor_user)
        response = client.get("/api/v1/auth/users/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["email"] == profesor_user.email

    def test_create_user_as_admin(self, auth_client, admin_user):
        client = auth_client(admin_user)
        data = {
            "email": "created@test.com",
            "password": "StrongPass1234",
            "first_name": "Created",
            "last_name": "User",
            "role": "PROFESOR",
        }
        response = client.post("/api/v1/auth/users/", data, format="json")
        assert response.status_code == 201
        assert User.objects.filter(email="created@test.com").exists()

    def test_create_user_as_profesor_forbidden(self, auth_client, profesor_user):
        client = auth_client(profesor_user)
        data = {
            "email": "forbidden@test.com",
            "password": "StrongPass1234",
            "first_name": "Forbidden",
            "last_name": "User",
            "role": "PROFESOR",
        }
        response = client.post("/api/v1/auth/users/", data, format="json")
        assert response.status_code == 403

    def test_update_user(self, auth_client, admin_user):
        target = UserFactory()
        client = auth_client(admin_user)
        response = client.patch(
            f"/api/v1/auth/users/{target.pk}/",
            {"first_name": "Updated"},
            format="json",
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.first_name == "Updated"

    def test_delete_self_prevented(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.delete(f"/api/v1/auth/users/{admin_user.pk}/")
        assert response.status_code == 400
        assert "eliminarse a si mismo" in response.data["detail"]

    def test_change_password(self, auth_client, admin_user):
        client = auth_client(admin_user)
        response = client.post(
            "/api/v1/auth/users/change-password/",
            {
                "old_password": "TestPass1234",
                "new_password": "NewSecure1234",
            },
            format="json",
        )
        assert response.status_code == 200
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewSecure1234")
