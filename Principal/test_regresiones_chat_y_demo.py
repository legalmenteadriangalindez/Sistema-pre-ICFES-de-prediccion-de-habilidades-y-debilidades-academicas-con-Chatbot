"""Regresiones del chat, el seguimiento y los cinco perfiles de demostración.

La IA se sustituye por mocks: la batería no descarga modelos ni necesita Ollama.
"""

import os
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from Principal.IA.LangGraph.graph_chatbot.chatbot import ModernChatbot
from Principal.models import (
    Estudiante, EstudianteAcudiente, IntentoEvaluacion, Matricula,
    Persona, PerfilUsuario, RespuestaEvaluacion, Rol,
)
from Principal.services.seguimiento import AREAS_BASE, resumen_estudiante


class EstadoConversacionesTests(SimpleTestCase):
    def crear_chatbot_falso(self, user_id="42"):
        chatbot = ModernChatbot.__new__(ModernChatbot)
        chatbot.user_id = user_id
        chatbot.checkpointer = MagicMock()
        chatbot.memory_manager = MagicMock()
        chatbot.app_graph = MagicMock()
        return chatbot

    def test_eliminar_conversacion_borra_checkpoints_y_metadata(self):
        bot = self.crear_chatbot_falso()
        bot.memory_manager.get_chat_info.return_value = {"chat_id": "chat-uno"}
        bot.memory_manager.delete_chat.return_value = True

        self.assertTrue(bot.delete_chat("chat-uno"))
        bot.checkpointer.delete_thread.assert_called_once_with("user_chat_42_chat-uno")
        bot.memory_manager.delete_chat.assert_called_once_with("chat-uno")

    def test_no_oculta_metadatos_si_falla_la_eliminacion_persistente(self):
        bot = self.crear_chatbot_falso()
        bot.memory_manager.get_chat_info.return_value = {"chat_id": "chat-uno"}
        bot.checkpointer.delete_thread.side_effect = RuntimeError("Disco ocupado")

        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.chatbot", level="ERROR"):
            self.assertFalse(bot.delete_chat("chat-uno"))
        bot.memory_manager.delete_chat.assert_not_called()

    def test_no_borra_identificadores_que_no_estan_en_el_historial(self):
        bot = self.crear_chatbot_falso()
        bot.memory_manager.get_chat_info.return_value = None

        self.assertFalse(bot.delete_chat("chat-ajeno"))
        bot.checkpointer.delete_thread.assert_not_called()

    def test_vaciar_conversacion_elimina_su_hilo_sin_quitarla_de_la_lista(self):
        bot = self.crear_chatbot_falso()
        self.assertTrue(bot.clear_conversation("chat-uno"))
        bot.checkpointer.delete_thread.assert_called_once_with("user_chat_42_chat-uno")
        bot.memory_manager.delete_chat.assert_not_called()

    def test_no_se_mezclan_hilos_de_distintos_usuarios(self):
        primero = self.crear_chatbot_falso(user_id="42")
        segundo = self.crear_chatbot_falso(user_id="43")
        self.assertTrue(primero.clear_conversation("igual-id"))
        self.assertTrue(segundo.clear_conversation("igual-id"))
        primero.checkpointer.delete_thread.assert_called_once_with("user_chat_42_igual-id")
        segundo.checkpointer.delete_thread.assert_called_once_with("user_chat_43_igual-id")

    def test_chat_devuelve_el_id_que_crea_y_lo_usa_para_el_checkpoint(self):
        from langchain_core.messages import AIMessage

        bot = self.crear_chatbot_falso()
        bot.memory_manager.get_chat_info.side_effect = [
            None, {"chat_id": "uuid-nuevo", "title": "Pregunta de matemáticas"}
        ]
        bot.memory_manager.create_new_chat.return_value = "uuid-nuevo"
        bot.app_graph.invoke.return_value = {"messages": [AIMessage(content="El resultado es cinco.")]}

        respuesta = bot.chat("¿Cuánto es dos más tres?", chat_id="default")

        self.assertTrue(respuesta["success"])
        self.assertEqual(respuesta["chat_id"], "uuid-nuevo")
        self.assertIn("cinco", respuesta["response"])
        self.assertEqual(
            bot.app_graph.invoke.call_args.args[1]["configurable"]["thread_id"],
            "user_chat_42_uuid-nuevo",
        )


class ContinuidadVistaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="estudiante_conversacion", password="Prueba!2026"
        )
        self.client.force_login(self.usuario)

    def preparar_bot(self):
        bot = MagicMock()
        bot.memory_manager.get_user_chats.return_value = []
        bot.memory_manager.get_cognitive_profile.return_value = {}
        bot.get_conversation_history.return_value = []
        return bot

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_primera_pregunta_guarda_uuid_y_segunda_reutiliza_el_mismo_hilo(self, obtener):
        bot = self.preparar_bot()
        bot.chat.side_effect = [
            {"success": True, "response": "Primera respuesta", "chat_id": "uuid-1"},
            {"success": True, "response": "Segunda respuesta", "chat_id": "uuid-1"},
        ]
        obtener.return_value = bot

        primero = self.client.post(reverse("home"), {
            "chat_id": "default", "prompt": "Primera pregunta",
        })
        self.assertEqual(primero.status_code, 200)
        self.assertEqual(primero.context["chat_id"], "uuid-1")
        self.assertEqual(self.client.session["chat_id_actual"], "uuid-1")

        segundo = self.client.post(reverse("home"), {"prompt": "Segunda pregunta"})
        self.assertEqual(segundo.status_code, 200)
        self.assertEqual(bot.chat.call_args_list[1].kwargs["chat_id"], "uuid-1")
        self.assertEqual(segundo.context["chat_id"], "uuid-1")

        pagina = self.client.get(reverse("home"))
        self.assertEqual(pagina.context["chat_id"], "uuid-1")

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_borrado_desde_vista_llama_a_eliminacion_persistente(self, obtener):
        bot = self.preparar_bot()
        bot.delete_chat.return_value = True
        obtener.return_value = bot

        self.client.post(reverse("home"), {"nuevo_chat": "1"})
        actual = self.client.session["chat_id_actual"]
        respuesta = self.client.post(reverse("home"), {
            "chat_id": actual, "delete_chat": "1",
        })
        self.assertRedirects(respuesta, reverse("home"), fetch_redirect_response=False)
        bot.delete_chat.assert_called_once_with(actual)
        self.assertNotIn("chat_id_actual", self.client.session)

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_borrado_fallido_muestra_error_sin_redirigir(self, obtener):
        bot = self.preparar_bot()
        bot.delete_chat.return_value = False
        obtener.return_value = bot
        respuesta = self.client.post(reverse("home"), {
            "chat_id": "chat-1", "delete_chat": "1",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("No se pudo eliminar", respuesta.context["chat_error"])


@override_settings(DEBUG=True)
class UsuariosDemoYSeguimientoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with patch.dict(os.environ, {"DJANGO_ENV": "development"}):
            call_command("crear_usuarios_prueba", verbosity=0)

    def test_las_cinco_cuentas_existen_y_pueden_autenticarse(self):
        for nombre in ("admin_demo", "estudiante_ana", "estudiante_luis",
                       "docente_demo", "acudiente_demo"):
            with self.subTest(usuario=nombre):
                self.assertTrue(get_user_model().objects.filter(username=nombre).exists())
                self.client.logout()
                self.assertTrue(self.client.login(
                    username=nombre, password="PreICFES2026!Demo"
                ))

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_cada_rol_va_a_su_vista_sin_cargar_ollama(self, obtener):
        bot = MagicMock()
        bot.memory_manager.get_user_chats.return_value = []
        bot.memory_manager.get_cognitive_profile.return_value = {}
        bot.get_conversation_history.return_value = []
        obtener.return_value = bot

        destinos = {
            "admin_demo": "admin_gestion_users",
            "docente_demo": "panel_docente",
            "acudiente_demo": "acudiente",
        }
        for usuario, vista in destinos.items():
            with self.subTest(usuario=usuario):
                self.client.force_login(get_user_model().objects.get(username=usuario))
                self.assertRedirects(
                    self.client.get(reverse("home")), reverse(vista),
                    fetch_redirect_response=False,
                )
                self.assertEqual(self.client.get(reverse(vista)).status_code, 200)
        for usuario in ("estudiante_ana", "estudiante_luis"):
            with self.subTest(usuario=usuario):
                self.client.force_login(get_user_model().objects.get(username=usuario))
                self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_acudiente_demo_solo_ve_estudiantes_vinculados(self):
        self.client.force_login(get_user_model().objects.get(username="acudiente_demo"))
        respuesta = self.client.get(reverse("acudiente"))
        self.assertEqual(respuesta.status_code, 200)
        ids_vinculados = {
            vinculo.estudiante_id for vinculo in EstudianteAcudiente.objects.filter(
                acudiente__persona__perfil_user__user__username="acudiente_demo"
            )
        }
        self.assertTrue(ids_vinculados)
        self.assertEqual(
            {fila["estudiante"].pk for fila in respuesta.context["hijos"]},
            ids_vinculados,
        )

    def test_integral_ampliado_alimenta_las_cinco_materias(self):
        persona = Persona.objects.get(perfil_user__user__username="estudiante_ana")
        estudiante = Estudiante.objects.get(persona=persona)
        intento = IntentoEvaluacion.objects.create(
            estudiante=estudiante, materia="Simulacro: Integral ampliado",
            total_preguntas=5, aciertos=3,
        )
        for numero, materia in enumerate(AREAS_BASE):
            RespuestaEvaluacion.objects.create(
                intento=intento, numero=numero,
                competencia=f"{materia} · Competencia de práctica",
                enunciado="", pregunta=f"Pregunta {numero}",
                opciones={"A": "Sí", "B": "No"},
                respuesta_estudiante="A", respuesta_correcta="A",
                explicacion="Respuesta de prueba", es_correcta=numero < 3,
            )
        resumen = resumen_estudiante(estudiante)
        por_area = {fila["nombre"]: fila for fila in resumen["areas"]}
        self.assertEqual(set(por_area), set(AREAS_BASE))
        for materia in AREAS_BASE:
            self.assertEqual(por_area[materia]["total"], 1)
        self.assertEqual(sum(fila["aciertos"] for fila in por_area.values()), 3)
