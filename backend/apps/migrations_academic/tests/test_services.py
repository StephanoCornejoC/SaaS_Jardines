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
        aula_3 = ClassroomFactory(nivel_edad=3)
        aula_5 = ClassroomFactory(nivel_edad=5)
        # Aula nivel 4 (destino para los de aula_3)
        ClassroomFactory(nivel_edad=4)

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
        aula_3 = ClassroomFactory(nivel_edad=3)
        aula_4 = ClassroomFactory(nivel_edad=4)

        student = StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        student.refresh_from_db()
        assert student.classroom == aula_4
        assert student.estado == "ACTIVO"
        assert migration.status == "EJECUTADO"
        assert migration.total_migrados == 1

    def test_graduates_level_5(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_5 = ClassroomFactory(nivel_edad=5)
        student = StudentFactory(classroom=aula_5, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        student.refresh_from_db()
        assert student.estado == "EGRESADO"
        assert student.classroom is None

    def test_creates_migration_log(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_3 = ClassroomFactory(nivel_edad=3)
        ClassroomFactory(nivel_edad=4)
        StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        assert migration.pk is not None
        assert migration.ejecutado_por == superadmin_user
        assert migration.anio_origen == current_year
        assert migration.anio_destino == current_year + 1

    def test_creates_detail_records(self, tenant, superadmin_user):
        current_year = date.today().year
        aula_3 = ClassroomFactory(nivel_edad=3)
        aula_4 = ClassroomFactory(nivel_edad=4)
        student = StudentFactory(classroom=aula_3, estado="ACTIVO")

        migration = execute_migration(current_year, superadmin_user)

        details = MigrationDetail.objects.filter(migration=migration)
        assert details.count() == 1
        detail = details.first()
        assert detail.student == student
        assert detail.aula_origen == aula_3
        assert detail.aula_destino == aula_4
        assert detail.estado_anterior == "ACTIVO"
        assert detail.estado_nuevo == "ACTIVO"


class TestCleanupOldData:
    """Tests del servicio `cleanup_graduated` / `cleanup_old_data`.

    Comportamiento ACTUAL (post-refactor): ELIMINA por completo los datos
    de alumnos egresados hace más de `years_to_keep` años. Antes se
    anonimizaba — ahora se elimina y los totales históricos quedan
    preservados en `MonthlyClosure`.

    Cascadas: borrar Student arrastra Guardian, MedicalRecord, Enrollment,
    MonthlyFee, Payment, Attendance, MigrationDetail.
    """

    def _create_old_graduated(self, tenant, superadmin_user, years_ago=3):
        """Helper: crea un alumno EGRESADO con una migración antigua."""
        current_year = date.today().year
        past_year = current_year - years_ago

        aula = ClassroomFactory(nivel_edad=5)
        student = StudentFactory(estado="EGRESADO", classroom=None)
        guardian = GuardianFactory(student=student, es_principal=True)
        medical = MedicalRecordFactory(student=student)

        migration = AcademicMigration.objects.create(
            anio_origen=past_year,
            anio_destino=past_year + 1,
            ejecutado_por=superadmin_user,
            status="EJECUTADO",
            total_migrados=1,
        )
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

    def test_returns_summary_dict(self, tenant, superadmin_user):
        """El servicio retorna un dict con conteos (alumnos_eliminados,
        transacciones_eliminadas, meses_auto_sellados, cutoff_year)."""
        self._create_old_graduated(tenant, superadmin_user, years_ago=3)

        result = cleanup_graduated(years_to_keep=2)

        assert isinstance(result, dict)
        assert "alumnos_eliminados" in result
        assert "transacciones_eliminadas" in result
        assert result["alumnos_eliminados"] >= 1

    def test_deletes_old_graduated_student(self, tenant, superadmin_user):
        """Alumno EGRESADO hace 3 años con years_to_keep=2 debe eliminarse."""
        from apps.students.models import Student

        student, _, _ = self._create_old_graduated(
            tenant, superadmin_user, years_ago=3
        )
        student_pk = student.pk

        cleanup_graduated(years_to_keep=2)

        assert not Student.objects.filter(pk=student_pk).exists()

    def test_respects_years_limit(self, tenant, superadmin_user):
        """Alumnos con enrollment reciente (dentro del periodo de retención)
        NO se eliminan. La lógica del servicio EXCLUYE alumnos con
        `enrollments__anio_escolar__gt=cutoff_year`.
        """
        from apps.enrollments.models import Enrollment
        from apps.students.models import Student
        from decimal import Decimal

        student, _, _ = self._create_old_graduated(
            tenant, superadmin_user, years_ago=1
        )
        # Agregamos un enrollment del año actual para que entre en la
        # ventana de retención (cutoff_year = current_year - 2 con
        # years_to_keep=2; un enrollment del año actual está por encima).
        current_year = date.today().year
        Enrollment.objects.create(
            student=student,
            anio_escolar=current_year,
            costo_matricula=Decimal("250.00"),
        )

        cleanup_graduated(years_to_keep=2)

        # Tiene enrollment reciente → permanece
        assert Student.objects.filter(pk=student.pk).exists()

    def test_rejects_zero_years(self, tenant):
        with pytest.raises(ValueError, match="al menos 1"):
            cleanup_graduated(years_to_keep=0)

    def test_rejects_excessive_years(self, tenant):
        with pytest.raises(ValueError, match="exceder"):
            cleanup_graduated(years_to_keep=11)

    def test_cascade_deletes_guardian_and_medical(self, tenant, superadmin_user):
        """Al eliminar el alumno, Guardian y MedicalRecord se borran en cascade."""
        from apps.students.models import Guardian, MedicalRecord

        _, guardian, medical = self._create_old_graduated(
            tenant, superadmin_user, years_ago=3
        )
        guardian_pk = guardian.pk
        medical_pk = medical.pk

        cleanup_graduated(years_to_keep=2)

        assert not Guardian.objects.filter(pk=guardian_pk).exists()
        assert not MedicalRecord.objects.filter(pk=medical_pk).exists()
