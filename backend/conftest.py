"""
Global conftest.py -- shared fixtures for all SAAS_COREM tests.

Strategy:
  - Uses django_tenants TenantTestCase patterns to create a test tenant
    with its own PostgreSQL schema.
  - Provides user fixtures for every role in the system.
  - Provides an `auth_client` helper that returns an APIClient already
    authenticated with a JWT for a given user.
"""

import pytest
from django.contrib.auth import get_user_model
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ---------------------------------------------------------------------------
# Tenant fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def setup_tenant(django_db_setup, django_db_blocker):
    """
    Create the public tenant + a test tenant once per session.
    django-tenants requires at least a public schema tenant to exist.
    """
    with django_db_blocker.unblock():
        TenantModel = get_tenant_model()
        DomainModel = get_tenant_domain_model()

        # Public tenant
        public, _ = TenantModel.objects.get_or_create(
            schema_name="public",
            defaults={
                "nombre": "Public",
                "ruc": "00000000000",
            },
        )
        DomainModel.objects.get_or_create(
            domain="localhost",
            tenant=public,
            defaults={"is_primary": True},
        )

        # Test tenant
        tenant, _ = TenantModel.objects.get_or_create(
            schema_name="test_jardin",
            defaults={
                "nombre": "Jardin Test",
                "ruc": "12345678901",
            },
        )
        DomainModel.objects.get_or_create(
            domain="test.localhost",
            tenant=tenant,
            defaults={"is_primary": True},
        )

        yield tenant

        # Cleanup is handled by the test DB teardown


@pytest.fixture()
def tenant(db, setup_tenant):
    """Return the test tenant, ensuring its schema is active."""
    from django.db import connection
    connection.set_tenant(setup_tenant)
    return setup_tenant


@pytest.fixture()
def tenant_client(tenant):
    """APIClient routed through the test tenant."""
    client = TenantClient(tenant)
    return client


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

def _create_user(email, role, **kwargs):
    """Helper to create a user with a known password."""
    defaults = {
        "first_name": role.capitalize(),
        "last_name": "Test",
        "role": role,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(email=email, password="TestPass1234", **defaults)
    return user


@pytest.fixture()
def superadmin_user(tenant):
    return _create_user("superadmin@test.com", "SUPERADMIN", is_staff=True, is_superuser=True)


@pytest.fixture()
def admin_user(tenant):
    return _create_user("admin@test.com", "ADMIN_JARDIN")


@pytest.fixture()
def director_user(tenant):
    return _create_user("director@test.com", "DIRECTOR")


@pytest.fixture()
def secretaria_user(tenant):
    return _create_user("secretaria@test.com", "SECRETARIA")


@pytest.fixture()
def profesor_user(tenant):
    return _create_user("profesor@test.com", "PROFESOR")


# ---------------------------------------------------------------------------
# Authenticated API client helper
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_client(tenant):
    """
    Returns a callable: auth_client(user) -> APIClient with Bearer token.
    Usage in tests:
        def test_something(auth_client, admin_user):
            client = auth_client(admin_user)
            response = client.get("/api/v1/...")
    """
    def _make_client(user):
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        # Set tenant header for django-tenants
        client.defaults["HTTP_HOST"] = "test.localhost"
        return client
    return _make_client
