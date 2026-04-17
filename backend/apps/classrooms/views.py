from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdminJardinOrAbove

from .models import Classroom
from .serializers import ClassroomDetailSerializer, ClassroomListSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Classroom.objects.select_related(
        "profesor_titular", "profesor_auxiliar"
    ).prefetch_related("students")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre"]
    filterset_fields = ["nivel_edad", "anio_escolar", "activo"]
    ordering_fields = ["nombre", "nivel_edad", "anio_escolar"]
    ordering = ["nivel_edad", "nombre"]

    def get_serializer_class(self):
        if self.action == "list":
            return ClassroomListSerializer
        return ClassroomDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminJardinOrAbove()]
        return [IsAuthenticated()]
