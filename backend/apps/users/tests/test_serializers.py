"""Unit tests for users.serializers."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.users.factories import ProfesorFactory, UserFactory
from apps.users.serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestUserSerializer:
    def test_fields_are_correct(self, tenant):
        user = UserFactory()
        serializer = UserSerializer(user)
        expected_fields = {"id", "email", "first_name", "last_name", "role", "telefono", "is_active"}
        assert set(serializer.data.keys()) == expected_fields

    def test_id_is_read_only(self, tenant):
        user = UserFactory()
        serializer = UserSerializer(user)
        assert "id" in serializer.fields
        assert serializer.fields["id"].read_only is True


class TestUserCreateSerializer:
    def _make_request(self, user):
        """Create a mock request with the given user."""
        factory = APIRequestFactory()
        request = factory.post("/fake/")
        request.user = user
        return request

    def test_valid_creation(self, tenant):
        admin = UserFactory(role="ADMIN_JARDIN")
        request = self._make_request(admin)
        data = {
            "email": "newuser@test.com",
            "password": "StrongPass1234",
            "first_name": "Nuevo",
            "last_name": "Usuario",
            "role": "PROFESOR",
        }
        serializer = UserCreateSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()
        assert user.check_password("StrongPass1234")
        assert user.role == "PROFESOR"

    def test_password_too_short(self, tenant):
        admin = UserFactory(role="ADMIN_JARDIN")
        request = self._make_request(admin)
        data = {
            "email": "short@test.com",
            "password": "123",
            "first_name": "Short",
            "last_name": "Pass",
            "role": "PROFESOR",
        }
        serializer = UserCreateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_duplicate_email(self, tenant):
        existing = UserFactory(email="dup@test.com")
        admin = UserFactory(role="ADMIN_JARDIN")
        request = self._make_request(admin)
        data = {
            "email": "dup@test.com",
            "password": "StrongPass1234",
            "first_name": "Dup",
            "last_name": "User",
            "role": "PROFESOR",
        }
        serializer = UserCreateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_role_escalation_prevention(self, tenant):
        """A DIRECTOR cannot create a SUPERADMIN."""
        director = UserFactory(role="DIRECTOR")
        request = self._make_request(director)
        data = {
            "email": "escalate@test.com",
            "password": "StrongPass1234",
            "first_name": "Escalate",
            "last_name": "Test",
            "role": "SUPERADMIN",
        }
        serializer = UserCreateSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "role" in serializer.errors

    def test_admin_can_create_director(self, tenant):
        """An ADMIN_JARDIN can create a DIRECTOR (lower in hierarchy)."""
        admin = UserFactory(role="ADMIN_JARDIN")
        request = self._make_request(admin)
        data = {
            "email": "newdir@test.com",
            "password": "StrongPass1234",
            "first_name": "New",
            "last_name": "Director",
            "role": "DIRECTOR",
        }
        serializer = UserCreateSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors


class TestChangePasswordSerializer:
    def _make_request(self, user):
        factory = APIRequestFactory()
        request = factory.post("/fake/")
        request.user = user
        return request

    def test_wrong_old_password(self, tenant):
        user = UserFactory()
        request = self._make_request(user)
        data = {"old_password": "WrongOldPass", "new_password": "NewSecure1234"}
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "old_password" in serializer.errors

    def test_valid_password_change(self, tenant):
        user = UserFactory(password="OldPass12345")
        request = self._make_request(user)
        data = {"old_password": "OldPass12345", "new_password": "NewSecure1234"}
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        user.refresh_from_db()
        assert user.check_password("NewSecure1234")
