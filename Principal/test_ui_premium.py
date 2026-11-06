"""Smoke tests for the redesigned interface; no Ollama server required."""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
class FrontendPremiumTests(TestCase):
    def test_admin_home_redirects_to_management(self):
        admin = get_user_model().objects.create_superuser(username="admin_ui", email="admin_ui@example.test", password="TestPassword123456!")
        self.client.force_login(admin)
        self.assertRedirects(self.client.get(reverse("home")), reverse("admin_gestion_users"), fetch_redirect_response=False)
    def test_student_dashboard_shows_accessible_chat_without_ollama(self):
        user = get_user_model().objects.create_user(username="alumno_ui", password="TestPassword123456!")
        self.client.force_login(user)
        with patch("Principal.views.chatbotManager.get_chatbot") as instance:
            instance.return_value.get_conversation_history.return_value=[]
            instance.return_value.memory_manager.get_user_chats.return_value=[]
            instance.return_value.memory_manager.get_cognitive_profile.return_value={}
            response=self.client.get(reverse("home"))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'id="chat-prompt"')
        self.assertContains(response,"data-chat-suggestion")
        self.assertContains(response,"css/ui-2026.css")
    def test_questionnaire_picker_preserves_subject_form(self):
        user = get_user_model().objects.create_user(username="quiz_ui", password="TestPassword123456!")
        self.client.force_login(user)
        response=self.client.get(reverse("test"))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"Cuestionarios de práctica")
        self.assertContains(response,'name="materia"')
        self.assertNotContains(response,"Respuesta generada por la IA:")
