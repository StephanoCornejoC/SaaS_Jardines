from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminJardinOrAbove

from apps.students.models import Guardian

from .models import Communication
from .serializers import CommunicationSerializer


class CommunicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Communication.objects.select_related("classroom", "enviado_por")
    serializer_class = CommunicationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "enviado"]
    search_fields = ["titulo", "contenido"]
    ordering_fields = ["created_at", "fecha_envio"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], url_path="enviar", permission_classes=[IsAdminJardinOrAbove])
    def enviar(self, request, pk=None):
        """
        Marca la comunicación como enviada y envía email a los apoderados relevantes.
        - GENERAL: todos los apoderados principales con email.
        - POR_AULA: solo los apoderados principales de alumnos del aula.
        """
        communication = self.get_object()

        if communication.enviado:
            return Response(
                {"error": "Esta comunicación ya fue enviada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener emails de apoderados relevantes
        guardians_qs = Guardian.objects.filter(
            es_principal=True
        ).exclude(email__isnull=True).exclude(email="")

        if communication.tipo == Communication.Tipo.POR_AULA:
            if not communication.classroom:
                return Response(
                    {"error": "Comunicación por aula requiere un aula asignada."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            guardians_qs = guardians_qs.filter(
                student__classroom=communication.classroom,
                student__estado="ACTIVO",
            )
        else:
            guardians_qs = guardians_qs.filter(student__estado="ACTIVO")

        emails = list(guardians_qs.values_list("email", flat=True).distinct())

        if not emails:
            return Response(
                {"error": "No se encontraron apoderados con email para enviar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enviar emails
        errores = []
        enviados = 0
        for email in emails:
            try:
                send_mail(
                    subject=communication.titulo,
                    message=communication.contenido,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                enviados += 1
            except Exception as e:
                errores.append({"email": email, "error": str(e)})

        # Marcar como enviado solo si al menos un email fue enviado exitosamente
        if enviados > 0:
            communication.enviado = True
            communication.fecha_envio = timezone.now()
            communication.save(update_fields=["enviado", "fecha_envio"])

        return Response(
            {
                "mensaje": f"Comunicación enviada a {enviados} apoderado(s).",
                "total_emails": len(emails),
                "enviados": enviados,
                "errores": errores,
            },
            status=status.HTTP_200_OK,
        )
