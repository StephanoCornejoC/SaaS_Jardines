"""Unit tests for users.permissions."""

import pytest
from unittest.mock import MagicMock

from apps.users.factories import UserFactory
from apps.users.permissions import IsAdminJardinOrAbove, IsSuperadmin

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _make_request(user):
    """Create a mock request with the given user."""
    request = MagicMock()
    request.user = user
    return request


class TestIsSuperadmin:
    perm = IsSuperadmin()

    def test_allows_superadmin(self, tenant):
        user = UserFactory(role="SUPERADMIN")
        request = _make_request(user)
        assert self.perm.has_permission(request, None) is True

    def test_denies_admin_jardin(self, tenant):
        user = UserFactory(role="ADMIN_JARDIN")
        request = _make_request(user)
        assert self.perm.has_permission(request, None) is False

    def test_denies_unauthenticated(self, tenant):
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        assert self.perm.has_permission(request, None) is False


class TestIsAdminJardinOrAbove:
    perm = IsAdminJardinOrAbove()

    def test_allows_admin_jardin(self, tenant):
        user = UserFactory(role="ADMIN_JARDIN")
        request = _make_request(user)
        assert self.perm.has_permission(request, None) is True

    def test_allows_superadmin(self, tenant):
        user = UserFactory(role="SUPERADMIN")
        request = _make_request(user)
        assert self.perm.has_permission(request, None) is True

    def test_denies_unauthenticated(self, tenant):
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        assert self.perm.has_permission(request, None) is False
