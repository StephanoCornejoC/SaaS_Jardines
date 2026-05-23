"""API / view tests for communications app."""

import pytest
from unittest.mock import patch

from apps.classrooms.factories import ClassroomFactory
from apps.communications.models import Communication
from apps.students.factories import GuardianFactory, StudentFactory

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestCommunicationViewSet:
    def test_create_communication(self, auth_client, admin_user):
        client = auth_client(admin_user)
        data = {
            "titulo": "Reunion de padres",
            "contenido": "Se convoca a reunion el viernes.",
            "tipo": "GENERAL",
        }
        response = client.post("/api/v1/communications/", data, format="json")
        assert response.status_code == 201
        assert response.data["enviado"] is False
        assert response.data["enviado_por"] == admin_user.pk

    @patch("apps.communications.views.send_mail")
    def test_enviar_queues_emails(self, mock_send_mail, auth_client, admin_user):
        """El endpoint /enviar/ encola el envío en background (threading) y
        responde 202 Accepted con un mensaje + total_emails + estado.

        NO verificamos el side-effect del send_mail (el thread es async y
        no es determinístico en tests). Para verificación end-to-end del
        envío, los tests de integración E2E con SMTP real.
        """
        student = StudentFactory(estado="ACTIVO")
        GuardianFactory(student=student, es_principal=True, email="parent@test.com")

        comm = Communication.objects.create(
            titulo="Aviso",
            contenido="Contenido del aviso",
            tipo="GENERAL",
            enviado_por=admin_user,
        )

        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/communications/{comm.pk}/enviar/",
            format="json",
        )
        assert response.status_code == 202, response.data
        assert "mensaje" in response.data
        assert response.data["total_emails"] >= 1
        assert response.data["estado"] == "encolado"

    def test_enviar_rejects_already_sent(self, auth_client, admin_user):
        """No se puede re-enviar una comunicación ya enviada."""
        student = StudentFactory(estado="ACTIVO")
        GuardianFactory(student=student, es_principal=True, email="parent@test.com")

        comm = Communication.objects.create(
            titulo="Ya enviada",
            contenido="Contenido",
            tipo="GENERAL",
            enviado_por=admin_user,
            enviado=True,
        )

        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/communications/{comm.pk}/enviar/",
            format="json",
        )
        assert response.status_code == 400
        assert "ya fue enviada" in response.data["error"]
