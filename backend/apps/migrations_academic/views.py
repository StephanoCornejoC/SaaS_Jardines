from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminJardinOrAbove, IsSuperadmin

from .models import AcademicMigration
from .serializers import (
    AcademicMigrationSerializer,
    MigrationPreviewSerializer,
)
from .services import cleanup_graduated, execute_migration, preview_migration


class AcademicMigrationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminJardinOrAbove]
    queryset = AcademicMigration.objects.prefetch_related(
        "details__student", "details__aula_origen", "details__aula_destino"
    ).select_related("ejecutado_por")
    serializer_class = AcademicMigrationSerializer

    @action(detail=False, methods=["get"], url_path="preview")
    def preview(self, request):
        """
        Vista previa de la migracion academica.
        Requiere query param 'anio_origen'.
        """
        anio_origen = request.query_params.get("anio_origen")
        if not anio_origen:
            return Response(
                {"error": "Se requiere el parámetro 'anio_origen'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preview_data = preview_migration(int(anio_origen))
        serializer = MigrationPreviewSerializer(preview_data)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="ejecutar", permission_classes=[IsSuperadmin])
    def ejecutar(self, request):
        """
        Ejecuta la migracion academica.
        Requiere campo 'anio_origen' en el body.
        """
        anio_origen = request.data.get("anio_origen")
        if not anio_origen:
            return Response(
                {"error": "Se requiere el campo 'anio_origen'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            migration = execute_migration(int(anio_origen), request.user)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AcademicMigrationSerializer(migration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="cleanup-egresados", permission_classes=[IsSuperadmin])
    def cleanup_egresados(self, request):
        """
        Anonimiza datos de alumnos egresados antiguos.
        Parametro opcional 'years_to_keep' (default: 2, minimo: 1, maximo: 10).
        """
        years_to_keep = request.data.get("years_to_keep", 2)

        try:
            years_to_keep = int(years_to_keep)
        except (TypeError, ValueError):
            return Response(
                {"error": "years_to_keep debe ser un numero entero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if years_to_keep < 1 or years_to_keep > 10:
            return Response(
                {"error": "years_to_keep debe estar entre 1 y 10."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            count = cleanup_graduated(years_to_keep)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": f"Se anonimizaron {count} alumnos egresados.",
                "total_procesados": count,
            }
        )
