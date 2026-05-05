from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .models import Guardian, MedicalRecord, Student
from .serializers import (
    GuardianSerializer,
    MedicalRecordSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Student.objects.select_related("classroom").prefetch_related(
        "apoderados", "ficha_medica"
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombres", "apellidos", "dni"]
    filterset_fields = ["estado", "classroom"]
    ordering_fields = ["apellidos", "nombres", "fecha_ingreso"]
    ordering = ["apellidos"]

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        return StudentDetailSerializer


class GuardianViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
