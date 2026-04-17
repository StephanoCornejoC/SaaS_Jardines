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
    def test_enviar_sends_emails(self, mock_send_mail, auth_client, admin_user):
        # Create student with guardian who has email
        student = StudentFactory(estado="ACTIVO")
        GuardianFactory(student=student, es_principal=True, email="parent@test.com")

        comm = Communication.objects.create(
            titulo="Aviso",
            contenido="Contenido del aviso",
            tipo="GENERAL",
            enviado_por=admin_user,
        )

        mock_send_mail.return_value = 1

        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/communications/{comm.pk}/enviar/",
            format="json",
        )
        assert response.status_code == 200
        assert response.data["enviados"] >= 1

        comm.refresh_from_db()
        assert comm.enviado is True
        assert comm.fecha_envio is not None

    def test_enviar_requires_admin(self, auth_client, profesor_user):
        comm = Communication.objects.create(
            titulo="Test",
            contenido="Content",
            tipo="GENERAL",
        )
        client = auth_client(profesor_user)
        response = client.post(
            f"/api/v1/communications/{comm.pk}/enviar/",
            format="json",
        )
        assert response.status_code == 403

    @patch("apps.communications.views.send_mail", side_effect=Exception("SMTP error"))
    def test_partial_failure_not_marked_sent(self, mock_send_mail, auth_client, admin_user):
        """If all emails fail, the communication is NOT marked as sent."""
        student = StudentFactory(estado="ACTIVO")
        GuardianFactory(student=student, es_principal=True, email="fail@test.com")

        comm = Communication.objects.create(
            titulo="Aviso Fallido",
            contenido="Este va a fallar",
            tipo="GENERAL",
            enviado_por=admin_user,
        )

        client = auth_client(admin_user)
        response = client.post(
            f"/api/v1/communications/{comm.pk}/enviar/",
            format="json",
        )
        assert response.status_code == 200
        assert response.data["enviados"] == 0
        assert len(response.data["errores"]) >= 1

        comm.refresh_from_db()
        assert comm.enviado is False
