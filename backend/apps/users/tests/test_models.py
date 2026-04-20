"""Unit tests for users.models.User."""

import pytest
from django.contrib.auth import get_user_model

from apps.users.factories import ProfesorFactory, SuperadminFactory, UserFactory

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestUserCreation:
    """Tests for User creation via the custom manager."""

    def test_create_user_with_email(self, tenant):
        user = User.objects.create_user(
            email="new@test.com",
            password="SecurePass99",
            first_name="Ana",
            last_name="Lopez",
        )
        assert user.email == "new@test.com"
        assert user.check_password("SecurePass99")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self, tenant):
        user = User.objects.create_superuser(
            email="super@test.com",
            password="SecurePass99",
            first_name="Root",
            last_name="Admin",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == "SUPERADMIN"

    def test_create_user_without_email_raises(self, tenant):
        with pytest.raises(ValueError, match="correo electr"):
            User.objects.create_user(email="", password="SecurePass99")

    def test_email_is_normalized(self, tenant):
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM",
            password="SecurePass99",
            first_name="Test",
            last_name="Norm",
        )
        assert user.email == "Test@example.com"

    def test_default_role_is_admin_jardin(self, tenant):
        """El producto comercial asigna ADMIN_JARDIN por defecto."""
        user = User.objects.create_user(
            email="default@test.com",
            password="SecurePass99",
            first_name="Default",
            last_name="Role",
        )
        assert user.role == User.Role.ADMIN_JARDIN


class TestUserRoleProperties:
    """Tests for the role helper properties."""

    def test_is_superadmin(self, tenant):
        user = SuperadminFactory()
        assert user.is_superadmin is True
        assert user.is_admin_jardin is False

    def test_is_admin_jardin(self, tenant):
        user = UserFactory(role="ADMIN_JARDIN")
        assert user.is_admin_jardin is True
        assert user.is_superadmin is False

    def test_is_director(self, tenant):
        user = UserFactory(role="DIRECTOR")
        assert user.is_director is True

    def test_is_secretaria(self, tenant):
        user = UserFactory(role="SECRETARIA")
        assert user.is_secretaria is True

    def test_is_profesor(self, tenant):
        user = ProfesorFactory()
        assert user.is_profesor is True


class TestUserStr:
    def test_str_representation(self, tenant):
        user = UserFactory(first_name="Maria", last_name="Garcia")
        assert "Maria Garcia" in str(user)
        assert user.email in str(user)
