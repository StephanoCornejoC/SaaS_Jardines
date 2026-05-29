from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.users.permissions import IsAdminJardinOrTeacherReadOnly

from .models import Classroom
from .serializers import ClassroomDetailSerializer, ClassroomListSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    # TEACHER puede LEER todas las aulas (necesita ver cualquiera para
    # cubrir asistencia cuando otra profesora falta). Modificar solo admin.
    permission_classes = [IsAdminJardinOrTeacherReadOnly]
    queryset = Classroom.objects.select_related(
        "profesor_titular", "profesor_auxiliar"
    ).prefetch_related("students")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre"]
    filterset_fields = ["nivel_edad"]
    ordering_fields = ["nombre", "nivel_edad"]
    ordering = ["nivel_edad", "nombre"]

    def get_serializer_class(self):
        if self.action == "list":
            return ClassroomListSerializer
        return ClassroomDetailSerializer
