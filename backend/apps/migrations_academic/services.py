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

    # Obtener alumnos activos con aula asignada en el anio origen
    students = Student.objects.filter(
        estado=Student.Estado.ACTIVO,
        classroom__anio_escolar=anio_origen,
    ).select_related("classroom")

    # Obtener aulas del anio destino
    aulas_destino = {
        aula.nivel_edad: aula
        for aula in Classroom.objects.filter(anio_escolar=anio_destino, activo=True)
    }

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

    # Obtener alumnos activos
    students = Student.objects.filter(
        estado=Student.Estado.ACTIVO,
        classroom__anio_escolar=anio_origen,
    ).select_related("classroom")

    # Obtener aulas del anio destino
    aulas_destino = {
        aula.nivel_edad: aula
        for aula in Classroom.objects.filter(anio_escolar=anio_destino, activo=True)
    }

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


def cleanup_graduated(years_to_keep=2):
    """
    Busca alumnos EGRESADO con mas de years_to_keep anios desde su ultimo
    detalle de migracion y los anonimiza (elimina datos personales sensibles).
    Usa soft-delete: anonimiza datos y marca estado ELIMINADO en lugar de
    borrar registros relacionados.
    Retorna la cantidad de alumnos procesados.
    """
    if years_to_keep < 1:
        raise ValueError("years_to_keep debe ser al menos 1")

    MAX_BATCH_SIZE = 500
    cutoff_date = timezone.now() - timedelta(days=years_to_keep * 365)

    # Alumnos egresados con migracion antigua
    old_graduated = Student.objects.filter(
        estado=Student.Estado.EGRESADO,
        migration_details__migration__fecha__lt=cutoff_date,
    ).distinct()[:MAX_BATCH_SIZE]

    count = 0
    for student in old_graduated:
        # Anonimizar datos personales (soft-delete)
        student.nombres = "ANONIMIZADO"
        student.apellidos = "ANONIMIZADO"
        student.dni = f"XXXX{student.id:04d}"
        student.foto = None
        student.estado = Student.Estado.ELIMINADO
        student.save(update_fields=["nombres", "apellidos", "dni", "foto", "estado", "updated_at"])

        # Anonimizar apoderados en lugar de eliminarlos
        for guardian in student.apoderados.all():
            guardian.nombres = "ANONIMIZADO"
            guardian.apellidos = "ANONIMIZADO"
            guardian.dni = f"XXXX{guardian.id:04d}"
            guardian.telefono = ""
            guardian.email = ""
            guardian.save(update_fields=["nombres", "apellidos", "dni", "telefono", "email"])

        # Anonimizar ficha medica en lugar de eliminarla
        if hasattr(student, "ficha_medica") and student.ficha_medica:
            ficha = student.ficha_medica
            ficha.observaciones = "ANONIMIZADO"
            ficha.alergias = "ANONIMIZADO"
            ficha.save(update_fields=["observaciones", "alergias"])

        count += 1

    return count
