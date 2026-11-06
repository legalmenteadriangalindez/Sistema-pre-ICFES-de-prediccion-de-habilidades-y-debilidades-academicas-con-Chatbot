"""Pruebas de acceso a la portada según los roles existentes del sistema."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario, Rol


class HomePorRolTests(TestCase):
    def test_superusuario_va_al_panel_de_gestion(self):
        admin = get_user_model().objects.create_superuser(
            username="admin_redireccion", email="admin@example.test", password="ClaveSegura!2026"
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response, reverse("admin_gestion_users"), fetch_redirect_response=False
        )

    def test_usuario_con_rol_admin_va_al_panel_sin_ser_superusuario(self):
        admin = get_user_model().objects.create_user(
            username="gestor_redireccion", password="ClaveSegura!2026"
        )
        perfil = PerfilUsuario.objects.create(user=admin)
        rol = Rol.objects.create(nombre="ADMIN")
        perfil.roles.add(rol)
        self.client.force_login(admin)

        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response, reverse("admin_gestion_users"), fetch_redirect_response=False
        )

    def test_inicio_de_sesion_admin_llega_a_panel(self):
        get_user_model().objects.create_superuser(
            username="admin_login", email="login@example.test", password="ClaveSegura!2026"
        )

        login = self.client.post(
            reverse("login"),
            {"username": "admin_login", "password": "ClaveSegura!2026"},
        )
        self.assertRedirects(login, reverse("home"), fetch_redirect_response=False)

        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response, reverse("admin_gestion_users"), fetch_redirect_response=False
        )

    def test_usuario_sin_rol_admin_conserva_vista_estudiantil(self):
        usuario = get_user_model().objects.create_user(
            username="estudiante_redireccion", password="ClaveSegura!2026"
        )
        self.client.force_login(usuario)

        # El acceso a la portada no debe requerir iniciar Ollama durante las pruebas.
        with patch("Principal.views.chatbotManager.get_chatbot") as chatbot, patch(
            "Principal.views.render", return_value=HttpResponse("Portada de estudiante")
        ) as render_view:
            chatbot.return_value.get_conversation_history.return_value = []
            chatbot.return_value.memory_manager.get_user_chats.return_value = []
            chatbot.return_value.memory_manager.get_cognitive_profile.return_value = {}
            response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render_view.call_args.args[1], "home.html")
