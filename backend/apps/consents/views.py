from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsAdminJardinOrAbove

from .models import Consent, ConsentDocument
from .serializers import ConsentDocumentSerializer, ConsentSerializer


def _client_ip(request):
    """IP real del cliente, respetando el proxy de Railway (X-Forwarded-For)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ConsentDocumentViewSet(viewsets.ModelViewSet):
    """
    Gestión de los documentos de consentimiento (las políticas versionadas).
    Solo la directora (ADMIN_JARDIN) o el superadmin los administran.
    """

    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = ConsentDocumentSerializer
    queryset = ConsentDocument.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["tipo", "activo", "obligatorio"]
    ordering_fields = ["tipo", "version", "vigente_desde"]


class ConsentViewSet(viewsets.ModelViewSet):
    """
    Registro y consulta de consentimientos otorgados/revocados.

    Al crear, la IP, el user-agent y el usuario que registra se capturan del
    request (no se confía en el cliente) — así el registro sirve como
    evidencia. Los consentimientos no se editan ni borran: para revertir uno,
    se registra una fila nueva con `otorgado=False`.
    """

    permission_classes = [IsAdminJardinOrAbove]
    serializer_class = ConsentSerializer
    queryset = Consent.objects.select_related(
        "documento", "student", "guardian", "registrado_por"
    )
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["student", "documento", "otorgado", "guardian"]
    ordering_fields = ["fecha", "created_at"]
    # Los consentimientos son evidencia: se agregan y consultan, no se mutan.
    http_method_names = ["get", "post", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(
            ip=_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:300],
            registrado_por=self.request.user if self.request.user.is_authenticated else None,
        )

    @action(detail=False, methods=["get"], url_path="estado-alumno")
    def estado_alumno(self, request):
        """
        Estado de consentimiento de un alumno frente a los documentos activos.

        Query params: student (id, obligatorio).

        Por cada documento activo devuelve si el alumno tiene el
        consentimiento vigente (su registro más reciente `otorgado=True`),
        y marca `pendiente=True` para los obligatorios sin otorgar. Sirve para
        que el front muestre "faltan N consentimientos" en la ficha del alumno.
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response({"detail": "El parámetro 'student' es obligatorio."}, status=400)

        documentos = ConsentDocument.objects.filter(activo=True)
        resultado = []
        pendientes = 0
        for doc in documentos:
            ultimo = (
                Consent.objects.filter(student_id=student_id, documento=doc)
                .order_by("-fecha")
                .first()
            )
            vigente = bool(ultimo and ultimo.otorgado)
            es_pendiente = doc.obligatorio and not vigente
            if es_pendiente:
                pendientes += 1
            resultado.append({
                "documento": doc.id,
                "tipo": doc.tipo,
                "tipo_display": doc.get_tipo_display(),
                "titulo": doc.titulo,
                "version": doc.version,
                "obligatorio": doc.obligatorio,
                "vigente": vigente,
                "pendiente": es_pendiente,
                "fecha": ultimo.fecha if ultimo else None,
            })

        return Response({
            "student": int(student_id),
            "pendientes": pendientes,
            "completo": pendientes == 0,
            "documentos": resultado,
        })
