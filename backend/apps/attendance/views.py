from datetime import date

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.classrooms.models import Classroom
from apps.users.permissions import IsTeacherOrAdmin

from .models import Attendance
from .serializers import (
    AttendanceReportSerializer,
    AttendanceSerializer,
    BulkAttendanceSerializer,
)


def _es_teacher(user):
    return user and user.is_authenticated and getattr(user, "role", None) == "TEACHER"


def _validar_fecha_teacher(user, fecha):
    """
    Bloquea a TEACHER de registrar/modificar asistencia de un día que no
    sea el de HOY. Errores de días anteriores los corrige la directora.
    """
    if _es_teacher(user) and fecha != date.today():
        raise PermissionDenied(
            "Como profesor solo puede registrar o modificar asistencia del día actual. "
            "Si necesita corregir una fecha anterior, contacte a la directora."
        )


class AttendanceViewSet(viewsets.ModelViewSet):
    # TEACHER + ADMIN. La restricción de "solo día actual" para TEACHER se
    # aplica explícitamente en cada acción de escritura más abajo.
    permission_classes = [IsTeacherOrAdmin]
    queryset = Attendance.objects.select_related(
        "student", "classroom", "registrado_por"
    )
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["classroom", "fecha", "estado"]
    ordering_fields = ["fecha", "created_at"]
    ordering = ["-fecha"]

    def perform_create(self, serializer):
        _validar_fecha_teacher(self.request.user, serializer.validated_data.get("fecha"))
        serializer.save()

    def perform_update(self, serializer):
        # En update la fecha puede venir o no — validamos contra la
        # instance.fecha si no llega un override.
        fecha = serializer.validated_data.get("fecha", serializer.instance.fecha)
        _validar_fecha_teacher(self.request.user, fecha)
        serializer.save()

    def perform_destroy(self, instance):
        _validar_fecha_teacher(self.request.user, instance.fecha)
        instance.delete()

    @action(detail=False, methods=["post"], url_path="registro-masivo")
    def registro_masivo(self, request):
        """
        Registro masivo de asistencia para un aula y fecha.
        Crea o actualiza la asistencia de todos los alumnos enviados.
        """
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        classroom_id = serializer.validated_data["classroom_id"]
        fecha = serializer.validated_data["fecha"]
        asistencias = serializer.validated_data["asistencias"]

        # TEACHER solo puede registrar masivamente la fecha de hoy.
        _validar_fecha_teacher(request.user, fecha)

        try:
            classroom = Classroom.objects.get(pk=classroom_id)
        except Classroom.DoesNotExist:
            return Response(
                {"error": "Aula no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # SECURITY: Validate that all student IDs belong to the specified
        # classroom to prevent recording attendance for unrelated students.
        student_ids = [item["student_id"] for item in asistencias]
        classroom_student_ids = set(
            classroom.students.values_list("id", flat=True)
        )
        invalid_ids = set(student_ids) - classroom_student_ids
        if invalid_ids:
            return Response(
                {"detail": f"Alumnos no pertenecen al aula: {invalid_ids}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        updated = 0

        for item in asistencias:
            obj, was_created = Attendance.objects.update_or_create(
                student_id=item["student_id"],
                fecha=fecha,
                defaults={
                    "classroom": classroom,
                    "estado": item["estado"],
                    "observaciones": item.get("observaciones", ""),
                    "registrado_por": request.user,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response(
            {
                "mensaje": f"Asistencia registrada: {created} creados, {updated} actualizados.",
                "fecha": str(fecha),
                "classroom_id": classroom_id,
                "total": len(asistencias),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="reporte-mensual")
    def reporte_mensual(self, request):
        """
        Reporte mensual de asistencia por alumno para un aula.
        Query params: classroom_id, mes, anio
        """
        classroom_id = request.query_params.get("classroom_id")
        mes = request.query_params.get("mes")
        anio = request.query_params.get("anio")

        if not all([classroom_id, mes, anio]):
            return Response(
                {"error": "Se requieren los parámetros: classroom_id, mes, anio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mes = int(mes)
            anio = int(anio)
            classroom_id = int(classroom_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Los parámetros mes, anio y classroom_id deben ser numéricos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendances = Attendance.objects.filter(
            classroom_id=classroom_id,
            fecha__month=mes,
            fecha__year=anio,
        )

        report = (
            attendances.values("student__id", "student__apellidos", "student__nombres")
            .annotate(
                total_presentes=Count(
                    "id", filter=Q(estado=Attendance.Estado.PRESENTE)
                ),
                total_ausentes=Count(
                    "id", filter=Q(estado=Attendance.Estado.AUSENTE)
                ),
                total_tardanzas=Count(
                    "id", filter=Q(estado=Attendance.Estado.TARDANZA)
                ),
                total_dias=Count("id"),
            )
            .order_by("student__apellidos", "student__nombres")
        )

        result = []
        for row in report:
            total = row["total_dias"]
            presentes = row["total_presentes"]
            porcentaje = (presentes / total * 100) if total > 0 else 0

            result.append(
                {
                    "student_id": row["student__id"],
                    "student_nombre": f"{row['student__apellidos']}, {row['student__nombres']}",
                    "total_presentes": presentes,
                    "total_ausentes": row["total_ausentes"],
                    "total_tardanzas": row["total_tardanzas"],
                    "porcentaje_asistencia": round(porcentaje, 2),
                }
            )

        serializer = AttendanceReportSerializer(result, many=True)
        return Response(serializer.data)
