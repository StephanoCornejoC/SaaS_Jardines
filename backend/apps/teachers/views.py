from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdminJardinOrAbove

from .models import Teacher, TeacherContract, TeacherPayment
from .serializers import (
    TeacherContractSerializer,
    TeacherDetailSerializer,
    TeacherListSerializer,
    TeacherPaymentSerializer,
)


class TeacherViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Teacher.objects.prefetch_related("contracts__payments")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombres", "apellidos", "dni"]
    ordering_fields = ["apellidos", "nombres", "fecha_ingreso"]
    ordering = ["apellidos"]

    def get_serializer_class(self):
        if self.action == "list":
            return TeacherListSerializer
        return TeacherDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminJardinOrAbove()]
        return [IsAuthenticated()]


class TeacherContractViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherContractSerializer

    def get_queryset(self):
        return TeacherContract.objects.filter(
            teacher_id=self.kwargs["teacher_pk"]
        ).prefetch_related("payments")

    def perform_create(self, serializer):
        teacher = get_object_or_404(Teacher, pk=self.kwargs["teacher_pk"])
        serializer.save(teacher=teacher)


class TeacherPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherPaymentSerializer

    def get_queryset(self):
        return TeacherPayment.objects.filter(
            contract_id=self.kwargs["contract_pk"],
            contract__teacher_id=self.kwargs["teacher_pk"],
        )

    def perform_create(self, serializer):
        contract = get_object_or_404(
            TeacherContract,
            pk=self.kwargs["contract_pk"],
            teacher_id=self.kwargs["teacher_pk"],
        )
        serializer.save(contract=contract)
