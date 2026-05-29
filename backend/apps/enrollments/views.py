from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.users.permissions import IsAdminJardinOrAbove

from .models import Enrollment
from .serializers import EnrollmentSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    # Matrículas son admin-only (incluye datos financieros).
    permission_classes = [IsAdminJardinOrAbove]
    queryset = Enrollment.objects.select_related("student", "classroom")
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["anio_escolar", "classroom", "student"]
    search_fields = ["student__nombres", "student__apellidos", "student__dni"]
    ordering_fields = ["anio_escolar", "fecha_matricula", "student__apellidos"]
    ordering = ["-anio_escolar", "student__apellidos"]
