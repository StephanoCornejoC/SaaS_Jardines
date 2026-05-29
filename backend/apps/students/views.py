from datetime import date

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.users.permissions import (
    IsAdminJardinOrAbove,
    IsAdminJardinOrTeacherReadOnly,
)

from .models import Guardian, MedicalRecord, Student
from .serializers import (
    GuardianSerializer,
    MedicalRecordSerializer,
    StudentDetailSerializer,
    StudentForTeacherSerializer,
    StudentListSerializer,
)


_MESES_ES = (
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


class StudentViewSet(viewsets.ModelViewSet):
    # TEACHER puede LEER (necesita la lista de alumnos del aula para tomar
    # asistencia); modificar es solo ADMIN_JARDIN. Datos sensibles se
    # filtran a nivel serializer en get_serializer_class().
    permission_classes = [IsAdminJardinOrTeacherReadOnly]
    queryset = Student.objects.select_related("classroom").prefetch_related(
        "apoderados", "ficha_medica"
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombres", "apellidos", "dni"]
    filterset_fields = ["estado", "classroom"]
    ordering_fields = ["apellidos", "nombres", "fecha_ingreso"]
    ordering = ["apellidos"]

    def get_serializer_class(self):
        # TEACHER siempre ve serializer "lite" sin datos sensibles (sin
        # apoderados, sin ficha médica, sin DNI).
        user = self.request.user if self.request else None
        if user and user.is_authenticated and getattr(user, "role", None) == "TEACHER":
            return StudentForTeacherSerializer
        if self.action == "list":
            return StudentListSerializer
        return StudentDetailSerializer

    @action(detail=False, methods=["get"], url_path="cumpleanios")
    def cumpleanios(self, request):
        """
        Lista los alumnos activos que cumplen años en un mes determinado.

        Query params:
          - mes (int, 1-12): default = mes actual

        Solo lista alumnos con estado=ACTIVO. Devuelve nombre, fecha de
        nacimiento, aula y edad que cumple. Ordenado por día del mes
        ascendente para que sea fácil ver "quién sigue esta semana".

        Restringido a admin (la profesora no necesita este módulo).
        """
        try:
            mes = int(request.query_params.get("mes", date.today().month))
        except (TypeError, ValueError):
            return Response({"detail": "El parámetro 'mes' debe ser un número entero."}, status=400)
        if mes < 1 or mes > 12:
            return Response({"detail": "El parámetro 'mes' debe estar entre 1 y 12."}, status=400)

        anio_actual = date.today().year

        qs = (
            Student.objects.filter(
                estado=Student.Estado.ACTIVO,
                fecha_nacimiento__month=mes,
            )
            .select_related("classroom")
            .order_by("fecha_nacimiento__day", "apellidos", "nombres")
        )

        data = []
        for s in qs:
            cumple_este_anio = date(
                anio_actual, s.fecha_nacimiento.month, s.fecha_nacimiento.day
            )
            edad_que_cumple = anio_actual - s.fecha_nacimiento.year
            data.append({
                "id": s.id,
                "nombres": s.nombres,
                "apellidos": s.apellidos,
                "foto": s.foto.url if s.foto else None,
                "classroom_nombre": s.classroom.nombre if s.classroom else None,
                "fecha_nacimiento": s.fecha_nacimiento,
                "dia": s.fecha_nacimiento.day,
                "cumple_este_anio": cumple_este_anio,
                "edad_que_cumple": edad_que_cumple,
            })

        return Response({
            "mes": mes,
            "mes_nombre": _MESES_ES[mes],
            "total": len(data),
            "cumpleanios": data,
        })

    # Cumpleaños es accesible para TEACHER y ADMIN_JARDIN (read-only).
    # Como ya el viewset permite GET a TEACHER (IsAdminJardinOrTeacherReadOnly),
    # no hace falta override de get_permissions para esta action.


class GuardianViewSet(viewsets.ModelViewSet):
    # Apoderados son datos sensibles — solo admin.
    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = GuardianSerializer

    def get_queryset(self):
        student_pk = self.kwargs.get("student_pk")
        # Verify student exists in current tenant schema
        student = get_object_or_404(Student, pk=student_pk)
        return Guardian.objects.filter(student=student)

    def perform_create(self, serializer):
        student = get_object_or_404(Student, pk=self.kwargs["student_pk"])
        serializer.save(student=student)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    # Ficha médica = dato sensible — solo admin.
    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = MedicalRecordSerializer
    http_method_names = ["get", "post", "put", "patch"]

    def get_queryset(self):
        student_pk = self.kwargs.get("student_pk")
        # Verify student exists in current tenant schema
        student = get_object_or_404(Student, pk=student_pk)
        return MedicalRecord.objects.filter(student=student)

    def perform_create(self, serializer):
        student = get_object_or_404(Student, pk=self.kwargs["student_pk"])
        serializer.save(student=student)
