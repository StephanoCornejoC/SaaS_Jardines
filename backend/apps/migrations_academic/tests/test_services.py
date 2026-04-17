"""Unit tests for migrations_academic.services."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone

from apps.classrooms.factories import ClassroomFactory
from apps.migrations_academic.models import AcademicMigration, MigrationDetail
from apps.migrations_academic.services import (
    cleanup_graduated,
    execute_migration,
    preview_migration,
)
from apps.students.factories import GuardianFactory, MedicalRecordFactory, StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestPreviewMigration:
    def test_returns_correct_counts(self, tenant):
        current_year = date.today().year
        # Create classrooms for current year
        aula_3 = ClassroomFactory(nivel_edad=3, anio_escolar=current_year)
        aula_5 = ClassroomFactory(nivel_edad=5, anio_escolar=current_year)
        # Create classrooms for next year
        ClassroomFactory(nivel_edad=4, anio_escolar=current_year + 1)

        # Students in aula_3 should promote
        s1 = StudentFactory(classroom=aula_3, estado="ACTIVO")
        s2 = StudentFactory(classroom=aula_3, estado="ACTIVO")
        # Student in aula_5 should graduate
        s3 = StudentFactory(classroom=aula_5, estado="ACTIVO")

        preview = preview_migration(current_year)

        assert preview["anio_origen"] == current_year
        assert preview["anio_destino"] == current_year + 1
        assert preview["total_alumnos"] == 3
        assert len(preview["promueven"]) == 2
        assert len(preview["egresan"]) == 1
        assert preview["egresan"][0]["accion"] == "EGRESA"


class TestExecuteMigration:
    def test_promotes_students(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_3 = ClassroomFactory(nivel_edad=3, anio_escolar=current_year)
        aula_4_next = ClassroomFactory(nivel_edad=4, anio_escolar=current_year + 1)

        student = StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        student.refresh_from_db()
        assert student.classroom == aula_4_next
        assert student.estado == "ACTIVO"
        assert migration.status == "EJECUTADO"
        assert migration.total_migrados == 1

    def test_graduates_level_5(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_5 = ClassroomFactory(nivel_edad=5, anio_escolar=current_year)
        student = StudentFactory(classroom=aula_5, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        student.refresh_from_db()
        assert student.estado == "EGRESADO"
        assert student.classroom is None

    def test_creates_migration_log(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_3 = ClassroomFactory(nivel_edad=3, anio_escolar=current_year)
        ClassroomFactory(nivel_edad=4, anio_escolar=current_year + 1)
        StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        assert migration.pk is not None
        assert migration.ejecutado_por == superadmin_user
        assert migration.anio_origen == current_year
        assert migration.anio_destino == current_year + 1

    def test_creates_detail_records(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_3 = ClassroomFactory(nivel_edad=3, anio_escolar=current_year)
        aula_4_next = ClassroomFactory(nivel_edad=4, anio_escolar=current_year + 1)
        student = StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        details = MigrationDetail.objects.filter(migration=migration)
        assert details.count() == 1
        detail = details.first()
        assert detail.student == student
        assert detail.aula_origen == aula_3
        assert detail.aula_destino == aula_4_next
        assert detail.estado_anterior == "ACTIVO"
        assert detail.estado_nuevo == "ACTIVO"


class TestCleanupGraduated:
    def _create_old_graduated(self, tenant, superadmin_user, years_ago=3):
        """Helper: create a graduated student with a migration from years_ago."""
        current_year = date.today().year
        past_year = current_year - years_ago

        aula = ClassroomFactory(nivel_edad=5, anio_escolar=past_year)
        student = StudentFactory(estado="EGRESADO", classroom=None)
        guardian = GuardianFactory(student=student, es_principal=True)
        medical = MedicalRecordFactory(student=student)

        # Create migration and backdate it
        migration = AcademicMigration.objects.create(
            anio_origen=past_year,
            anio_destino=past_year + 1,
            ejecutado_por=superadmin_user,
            status="EJECUTADO",
            total_migrados=1,
        )
        # Backdate the migration fecha
        AcademicMigration.objects.filter(pk=migration.pk).update(
            fecha=timezone.now() - timedelta(days=years_ago * 365 + 10)
        )

        MigrationDetail.objects.create(
            migration=migration,
            student=student,
            aula_origen=aula,
            aula_destino=None,
            estado_anterior="ACTIVO",
            estado_nuevo="EGRESADO",
        )

        return student, guardian, medical

    def test_anonymizes_data(self, tenant, superadmin_user):
        student, guardian, medical = self._create_old_graduated(
            tenant, superadmin_user, years_ago=3
        )
        original_name = student.nombres

        count = cleanup_graduated(years_to_keep=2)

        assert count >= 1
        student.refresh_from_db()
        assert student.nombres == "ANONIMIZADO"
        assert student.apellidos == "ANONIMIZADO"
        assert student.dni.startswith("XXXX")

    def test_respects_years_limit(self, tenant, superadmin_user):
        """Students within the retention period should NOT be anonymized."""
        student, _, _ = self._create_old_graduated(
            tenant, superadmin_user, years_ago=1
        )

        count = cleanup_graduated(years_to_keep=2)

        student.refresh_from_db()
        # Student is within 2-year window -- should not be anonymized
        assert student.nombres != "ANONIMIZADO"

    def test_rejects_zero_years(self, tenant):
        with pytest.raises(ValueError, match="al menos 1"):
            cleanup_graduated(years_to_keep=0)

    def test_anonymizes_guardians(self, tenant, superadmin_user):
        student, guardian, _ = self._create_old_graduated(
            tenant, superadmin_user, years_ago=3
        )

        cleanup_graduated(years_to_keep=2)

        guardian.refresh_from_db()
        assert guardian.nombres == "ANONIMIZADO"
        assert guardian.telefono == ""

    def test_anonymizes_medical_record(self, tenant, superadmin_user):
        student, _, medical = self._create_old_graduated(
            tenant, superadmin_user, years_ago=3
        )

        cleanup_graduated(years_to_keep=2)

        medical.refresh_from_db()
        assert medical.observaciones == "ANONIMIZADO"
        assert medical.alergias == "ANONIMIZADO"
