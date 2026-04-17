"""API / view tests for migrations_academic app."""

import pytest
from datetime import date

from apps.classrooms.factories import ClassroomFactory
from apps.students.factories import StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestAcademicMigrationViewSet:
    def test_preview_as_admin(self, auth_client, admin_user):
        current_year = date.today().year
        aula = ClassroomFactory(nivel_edad=3, anio_escolar=current_year)
        StudentFactory(classroom=aula, estado="ACTIVO")

        client = auth_client(admin_user)
        response = client.get(
            f"/api/v1/migrations/preview/?anio_origen={current_year}"
        )
        assert response.status_code == 200
        assert response.data["anio_origen"] == current_year
        assert response.data["total_alumnos"] >= 1

    def test_ejecutar_requires_superadmin(self, auth_client, admin_user, superadmin_user):
        """Only SUPERADMIN can execute migrations."""
        current_year = date.today().year

        # Admin should be denied
        client_admin = auth_client(admin_user)
        response = client_admin.post(
            "/api/v1/migrations/ejecutar/",
            {"anio_origen": current_year},
            format="json",
        )
        assert response.status_code == 403

        # Superadmin should succeed (even if no students, it creates a migration)
        client_super = auth_client(superadmin_user)
        response = client_super.post(
            "/api/v1/migrations/ejecutar/",
            {"anio_origen": current_year},
            format="json",
        )
        assert response.status_code == 201

    def test_cleanup_requires_superadmin(self, auth_client, admin_user, superadmin_user):
        # Admin should be denied
        client_admin = auth_client(admin_user)
        response = client_admin.post(
            "/api/v1/migrations/cleanup-egresados/",
            {"years_to_keep": 2},
            format="json",
        )
        assert response.status_code == 403

        # Superadmin should succeed
        client_super = auth_client(superadmin_user)
        response = client_super.post(
            "/api/v1/migrations/cleanup-egresados/",
            {"years_to_keep": 2},
            format="json",
        )
        assert response.status_code == 200

    def test_profesor_cannot_execute_migration(self, auth_client, profesor_user):
        current_year = date.today().year
        client = auth_client(profesor_user)
        response = client.post(
            "/api/v1/migrations/ejecutar/",
            {"anio_origen": current_year},
            format="json",
        )
        assert response.status_code == 403

    def test_cleanup_validates_years(self, auth_client, superadmin_user):
        client = auth_client(superadmin_user)

        # years_to_keep = 0 should fail
        response = client.post(
            "/api/v1/migrations/cleanup-egresados/",
            {"years_to_keep": 0},
            format="json",
        )
        assert response.status_code == 400

        # years_to_keep = 11 should fail
        response = client.post(
            "/api/v1/migrations/cleanup-egresados/",
            {"years_to_keep": 11},
            format="json",
        )
        assert response.status_code == 400
