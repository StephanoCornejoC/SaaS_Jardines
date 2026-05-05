import re
from urllib.parse import quote

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.students.models import Guardian

from .models import Communication
from .serializers import CommunicationSerializer


def _normalizar_telefono(telefono):
    if not telefono:
        return None
    solo_digitos = re.sub(r"\D", "", telefono)
    if not solo_digitos:
        return None
    if len(solo_digitos) == 9:
        solo_digitos = "51" + solo_digitos
    return solo_digitos


def _resolver_destinatarios(communication):
    guardians_qs = Guardian.objects.select_related("student").filter(
        student__estado="ACTIVO"
    )
    if communication.tipo == Communication.Tipo.POR_AULA and communication.classroom:
        guardians_qs = guardians_qs.filter(student__classroom=communication.classroom)
    return guardians_qs


class CommunicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Communication.objects.select_related("classroom", "enviado_por")
    serializer_class = CommunicationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "enviado"]
    search_fields = ["titulo", "contenido"]
    ordering_fields = ["created_at", "fecha_envio"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["get"], url_path="destinatarios")
    def destinatarios(self, request, pk=None):
        """Devuelve apoderados únicos (deduplicados por teléfono/correo)."""
        communication = self.get_object()
        if communication.tipo == Communication.Tipo.POR_AULA and not communication.classroom:
            return Response(
                {"error": "Comunicación por aula requiere un aula asignada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        guardians = _resolver_destinatarios(communication).order_by(
            "student__apellidos", "apellidos"
        )

        vistos = set()
        data = []
        for g in guardians:
            # Clave de dedup: teléfono o email. Un mismo apoderado de varios
            # hermanos solo aparece una vez.
            key = _normalizar_telefono(g.telefono) or (g.email or "").lower()
            if not key or key in vistos:
                continue
            vistos.add(key)
            data.append({
                "id": g.id,
                "nombres": f"{g.nombres} {g.apellidos}",
                "alumno": str(g.student),
                "telefono": g.telefono,
                "email": g.email or "",
                "parentesco": g.parentesco,
                "es_principal": g.es_principal,
            })
        return Response({"total": len(data), "destinatarios": data})

    @action(detail=True, methods=["post"], url_path="enviar", permission_classes=[IsAuthenticated])
    def enviar(self, request, pk=None):
        """Envía la comunicación por email a los apoderados con correo registrado."""
        communication = self.get_object()

        if communication.enviado:
            return Response(
                {"error": "Esta comunicación ya fue enviada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if communication.tipo == Communication.Tipo.POR_AULA and not communication.classroom:
            return Response(
                {"error": "Comunicación por aula requiere un aula asignada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guardians_qs = _resolver_destinatarios(communication)
        # Deduplicar emails (un padre con varios hijos solo recibe 1 mail)
        emails = sorted({
            (e or "").strip().lower()
            for e in guardians_qs.values_list("email", flat=True)
            if e
        })

        if not emails:
            return Response(
                {"error": "No se encontraron apoderados con email registrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

    @action(detail=True, methods=["post"], url_path="whatsapp", permission_classes=[IsAuthenticated])
    def whatsapp(self, request, pk=None):
        """
        Devuelve enlaces wa.me listos para abrir desde el navegador.
        El frontend abre cada enlace en una pestaña; no requiere API externa ni costo.
        """
        communication = self.get_object()

        if communication.tipo == Communication.Tipo.POR_AULA and not communication.classroom:
            return Response(
                {"error": "Comunicación por aula requiere un aula asignada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guardians_qs = _resolver_destinatarios(communication)
        mensaje = f"*{communication.titulo}*\n\n{communication.contenido}"
        mensaje_codificado = quote(mensaje)

        enlaces = []
        sin_telefono = 0
        # Deduplicar por número normalizado (un padre de varios hijos = 1 chat)
        vistos = set()
        for g in guardians_qs:
            telefono = _normalizar_telefono(g.telefono)
            if not telefono:
                sin_telefono += 1
                continue
            if telefono in vistos:
                continue
            vistos.add(telefono)
            enlaces.append(
                {
                    "destinatario": f"{g.nombres} {g.apellidos}",
                    "alumno": str(g.student),
                    "telefono": g.telefono,
                    "url": f"https://wa.me/{telefono}?text={mensaje_codificado}",
                }
            )

        if not enlaces:
            return Response(
                {"error": "No hay apoderados con teléfono válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not communication.enviado:
            communication.enviado = True
            communication.fecha_envio = timezone.now()
            communication.save(update_fields=["enviado", "fecha_envio"])

        return Response(
            {
                "total": len(enlaces),
                "sin_telefono": sin_telefono,
                "enlaces": enlaces,
            }
        )
