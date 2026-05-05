from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.classrooms.models import Classroom
from apps.students.models import Student

from .models import AcademicMigration, MigrationDetail


def preview_migration(anio_origen):
    """
    Genera una vista previa de lo que ocurriria con la migracion academica.
    NO modifica la base de datos.
    Retorna un dict con el resumen de la migracion.
    """
    anio_destino = anio_origen + 1

    # Obtener alumnos activos con aula asignada
    students = Student.objects.filter(
        estado=Student.Estado.ACTIVO,
        classroom__isnull=False,
    ).select_related("classroom")

    # Las aulas son permanentes; basta con indexarlas por nivel_edad
    aulas_destino = {aula.nivel_edad: aula for aula in Classroom.objects.all()}

    preview = {
        "anio_origen": anio_origen,
        "anio_destino": anio_destino,
        "total_alumnos": students.count(),
        "por_nivel": [],
        "promueven": [],
        "egresan": [],
        "sin_aula_destino": [],
    }

    for student in students:
        nivel_actual = student.classroom.nivel_edad if student.classroom else None

        if nivel_actual is None:
            continue

        if nivel_actual == 5:
            # Alumnos de 5 anios egresan
            preview["egresan"].append({
                "student_id": student.id,
                "student_nombre": str(student),
                "aula_origen": str(student.classroom),
                "nivel_actual": nivel_actual,
                "accion": "EGRESA",
            })
        else:
            # Alumnos promueven al siguiente nivel
            nivel_destino = nivel_actual + 1
            aula_destino = aulas_destino.get(nivel_destino)

            detail = {
                "student_id": student.id,
                "student_nombre": str(student),
                "aula_origen": str(student.classroom),
                "nivel_actual": nivel_actual,
                "nivel_destino": nivel_destino,
                "aula_destino": str(aula_destino) if aula_destino else None,
                "accion": "PROMUEVE",
            }

            if aula_destino:
                preview["promueven"].append(detail)
            else:
                detail["accion"] = "SIN_AULA_DESTINO"
                preview["sin_aula_destino"].append(detail)

    # Resumen por nivel
    niveles = {}
    for student in students:
        if student.classroom:
            nivel = student.classroom.nivel_edad
            if nivel not in niveles:
                niveles[nivel] = {"nivel": nivel, "cantidad": 0, "accion": ""}
            niveles[nivel]["cantidad"] += 1
            niveles[nivel]["accion"] = "EGRESA" if nivel == 5 else f"PROMUEVE a {nivel + 1} años"

    preview["por_nivel"] = sorted(niveles.values(), key=lambda x: x["nivel"])

    return preview


@transaction.atomic
def execute_migration(anio_origen, user):
    """
    Ejecuta la migracion academica: promueve alumnos al siguiente nivel,
    marca como EGRESADO a los de 5 anios.
    Crea registros de AcademicMigration y MigrationDetail.
    Retorna el registro de AcademicMigration.
    """
    anio_destino = anio_origen + 1

    # Crear registro de migracion
    migration = AcademicMigration.objects.create(
        anio_origen=anio_origen,
        anio_destino=anio_destino,
        ejecutado_por=user,
        status=AcademicMigration.Status.EJECUTADO,
    )

    # Obtener alumnos activos con aula asignada
    students = Student.objects.filter(
        estado=Student.Estado.ACTIVO,
        classroom__isnull=False,
    ).select_related("classroom")

    aulas_destino = {aula.nivel_edad: aula for aula in Classroom.objects.all()}

    total_migrados = 0

    for student in students:
        nivel_actual = student.classroom.nivel_edad if student.classroom else None

        if nivel_actual is None:
            continue

        aula_origen = student.classroom
        estado_anterior = student.estado

        if nivel_actual == 5:
            # Egresa
            student.estado = Student.Estado.EGRESADO
            student.classroom = None
            student.save(update_fields=["estado", "classroom", "updated_at"])

            MigrationDetail.objects.create(
                migration=migration,
                student=student,
                aula_origen=aula_origen,
                aula_destino=None,
                estado_anterior=estado_anterior,
                estado_nuevo=Student.Estado.EGRESADO,
            )
        else:
            # Promueve al siguiente nivel
            nivel_destino = nivel_actual + 1
            aula_destino = aulas_destino.get(nivel_destino)

            student.classroom = aula_destino
            student.save(update_fields=["classroom", "updated_at"])

            MigrationDetail.objects.create(
                migration=migration,
                student=student,
                aula_origen=aula_origen,
                aula_destino=aula_destino,
                estado_anterior=estado_anterior,
                estado_nuevo=Student.Estado.ACTIVO,
            )

        total_migrados += 1

    migration.total_migrados = total_migrados
    migration.save(update_fields=["total_migrados"])

    return migration


def cleanup_old_data(years_to_keep=2):
    """
    Elimina por completo los datos de alumnos egresados hace más de
    `years_to_keep` años. Conserva los `MonthlyClosure` (totales agregados).

    Antes de eliminar, asegura que cada mes con transacciones del periodo a
    purgar tenga su `MonthlyClosure` (auto-sello del periodo).

    Cascadas que se aplican al borrar `Student`:
        - Guardian (CASCADE)
        - MedicalRecord (CASCADE)
        - Enrollment (CASCADE)
        - MonthlyFee (CASCADE) → arrastra Payment
        - Payment (CASCADE)
        - Attendance (CASCADE)
        - MigrationDetail (CASCADE)
        - CashTransaction.referencia_pago (SET_NULL): la transacción queda
          como "ingreso histórico sin referencia al alumno". Si la fecha de
          la transacción también está fuera del periodo de retención, se
          elimina (los totales ya quedaron en MonthlyClosure).

    Devuelve un dict con el detalle de lo eliminado.
    """
    from apps.cashflow.models import CashTransaction, MonthlyClosure
    from apps.cashflow.services import close_month

    if years_to_keep < 1:
        raise ValueError("years_to_keep debe ser al menos 1")
    if years_to_keep > 10:
        raise ValueError("years_to_keep no debe exceder 10")

    today = timezone.now().date()
    cutoff_year = today.year - years_to_keep

    with transaction.atomic():
        # 1. Auto-sellar meses anteriores al cutoff que no tengan cierre.
        anios_a_sellar = (
            CashTransaction.objects.filter(fecha__year__lte=cutoff_year)
            .values_list("fecha__year", "fecha__month")
            .distinct()
        )
        cierres_creados = 0
        for anio, mes in anios_a_sellar:
            if not MonthlyClosure.objects.filter(mes=mes, anio=anio).exists():
                close_month(mes, anio, user=None)
                cierres_creados += 1

        # 2. Identificar alumnos a eliminar: egresados + sin actividad reciente.
        alumnos_purgar = Student.objects.filter(
            estado=Student.Estado.EGRESADO,
        ).exclude(
            enrollments__anio_escolar__gt=cutoff_year,
        ).distinct()
        total_alumnos = alumnos_purgar.count()

        # 3. Eliminar transacciones de caja del periodo a purgar.
        #    Sus totales ya están preservados en MonthlyClosure.
        tx_purgar = CashTransaction.objects.filter(fecha__year__lte=cutoff_year)
        total_tx = tx_purgar.count()
        tx_purgar.delete()

        # 4. Eliminar alumnos (cascade limpia el resto).
        alumnos_purgar.delete()

    return {
        "alumnos_eliminados": total_alumnos,
        "transacciones_eliminadas": total_tx,
        "meses_auto_sellados": cierres_creados,
        "cutoff_year": cutoff_year,
        "years_to_keep": years_to_keep,
    }


# Alias retro-compatible: el endpoint y los tests usaban el nombre viejo.
cleanup_graduated = cleanup_old_data
