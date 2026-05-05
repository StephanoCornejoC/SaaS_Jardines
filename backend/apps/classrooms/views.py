from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Classroom
from .serializers import ClassroomDetailSerializer, ClassroomListSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
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
