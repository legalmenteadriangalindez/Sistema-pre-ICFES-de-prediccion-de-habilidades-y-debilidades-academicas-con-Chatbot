"""Regresiones de fase 8: GET solo consulta, POST procesa y recuerdos sin duplicados."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from langchain_core.messages import AIMessage, HumanMessage

from Principal.IA.LangGraph.graph_chatbot.chatbot import extraer_y_guardar_recuerdo
from Principal.models import (
    AnalisisCognitivo,
    EstiloAprendizaje,
    Estudiante,
    NivelAprendizaje,
    PerfilPedagogico,
    PerfilUsuario,
    Persona,
    RitmoAprendizaje,
    Sexo,
)
from Principal.services.tutor_profile_sync import (
    seleccionar_perfil_cognitivo,
    sincronizar_perfil_academico,
)


class ContratoMemoriaGrafoTests(SimpleTestCase):
    def test_extraccion_se_almacena_una_vez_y_el_grafo_no_duplica_vectores(self):
        memoria = MagicMock()
        memoria.extract_and_store_memories.return_value = True
        state = {"messages": [HumanMessage(content="Me gusta aprender matemáticas")]}
        changed = extraer_y_guardar_recuerdo(state, memoria)
        self.assertEqual(
            changed, {"last_memory_extraction": "Me gusta aprender matemáticas"}
        )
        memoria.extract_and_store_memories.assert_called_once_with(
            "Me gusta aprender matemáticas"
        )
        memoria.save_memory_vectorial.assert_not_called()
        self.assertEqual(extraer_y_guardar_recuerdo({**state, **changed}, memoria), {})
        memoria.extract_and_store_memories.assert_called_once()

    def test_extractor_booleano_false_no_se_reinterpreta_como_lista(self):
        memoria = MagicMock()
        memoria.extract_and_store_memories.return_value = False
        state = {"messages": [AIMessage(content="Hola"), HumanMessage(content="¿Qué es álgebra?")]}
        self.assertEqual(
            extraer_y_guardar_recuerdo(state, memoria),
            {"last_memory_extraction": "¿Qué es álgebra?"},
        )
        memoria.save_memory_vectorial.assert_not_called()

    def test_error_de_extraccion_no_revela_el_mensaje_ni_rompe_el_grafo(self):
        memoria = MagicMock()
        memoria.extract_and_store_memories.side_effect = OSError("servicio caído")
        with self.assertLogs(
            "Principal.IA.LangGraph.graph_chatbot.chatbot", level="WARNING"
        ) as logs:
            result = extraer_y_guardar_recuerdo(
                {"messages": [HumanMessage(content="dato muy privado")]}, memoria
            )
        self.assertEqual(result, {})
        self.assertNotIn("dato muy privado", " ".join(logs.output))
        memoria.save_memory_vectorial.assert_not_called()

    def test_extraccion_vacia_o_sin_mensaje_humano_no_almacena(self):
        memoria = MagicMock()
        for messages in ([], [AIMessage(content="Tutor")], [HumanMessage(content="  ")]):
            with self.subTest(messages=messages):
                self.assertEqual(
                    extraer_y_guardar_recuerdo({"messages": messages}, memoria), {}
                )
        memoria.extract_and_store_memories.assert_not_called()

    def test_perfil_de_lista_respeta_usuario_y_descarta_datos_incompletos(self):
        perfil = {
            "user_id": "42",
            "general_level": "Alto",
            "area": "Ciencias",
            "strong_areas": ["Biología"],
            "weak_areas": ["Física"],
            "frequent_mistakes": ["Unidades"],
        }
        self.assertEqual(
            seleccionar_perfil_cognitivo(
                [{"user_id": "77", **{k: v for k, v in perfil.items() if k != "user_id"}}, perfil],
                "42",
            ),
            perfil,
        )
        self.assertIsNone(seleccionar_perfil_cognitivo([perfil], "77"))
        self.assertIsNone(
            seleccionar_perfil_cognitivo({**perfil, "strong_areas": "No es lista"}, "42")
        )


class VistaChatbotSeparadaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="estudiante_fase8", password="ClaveFase8!2026"
        )
        perfil = PerfilUsuario.objects.create(user=cls.user)
        sexo = Sexo.objects.create(descripcion="Prueba fase 8")
        persona = Persona.objects.create(
            perfil_user=perfil,
            nombre="Alumno",
            apellido="Fase Ocho",
            documento="FASE8-DOC-001",
            fecha_nacimiento="2008-01-01",
            direccion="Calle de prueba",
            telefono="3000000000",
            sexo=sexo,
        )
        cls.estudiante = Estudiante.objects.create(persona=persona)

    def setUp(self):
        self.client.force_login(self.user)
        self.bot = MagicMock()
        self.bot.get_conversation_history.return_value = []
        self.bot.memory_manager.get_user_chats.return_value = []
        self.perfil = {
            "user_id": str(self.user.pk),
            "general_level": "Alto",
            "area": "Matemáticas",
            "strong_areas": ["Álgebra"],
            "weak_areas": ["Geometría"],
            "frequent_mistakes": ["Signos"],
        }
        self.bot.memory_manager.get_cognitive_profile.return_value = [self.perfil]
        self.bot.chat.return_value = {
            "success": True,
            "response": "Practiquemos geometría",
            "chat_id": "uuid-fase8",
        }
        self.patcher = patch(
            "Principal.views.chatbotManager.get_chatbot", return_value=self.bot
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_get_muestra_perfil_sin_escribir_tablas_academicas(self):
        for _ in range(2):
            response = self.client.get(reverse("home"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["profile"], [self.perfil])
            self.assertEqual(response.context["inicio_intentos"], 0)
            self.assertEqual(response.context["chat_id"], "default")
        for model in (
            NivelAprendizaje,
            RitmoAprendizaje,
            EstiloAprendizaje,
            PerfilPedagogico,
            AnalisisCognitivo,
        ):
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.count(), 0)
        self.bot.chat.assert_not_called()

    def test_post_exitoso_actualiza_perfiles_y_mantiene_contexto_y_sesion(self):
        response = self.client.post(reverse("home"), {"prompt": "Explícame fracciones"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["response"], "Practiquemos geometría")
        self.assertEqual(response.context["chat_id"], "uuid-fase8")
        self.assertEqual(self.client.session["chat_id_actual"], "uuid-fase8")
        self.assertEqual(PerfilPedagogico.objects.filter(estudiante=self.estudiante).count(), 1)
        self.assertEqual(AnalisisCognitivo.objects.filter(estudiante=self.estudiante).count(), 1)
        self.assertEqual(
            AnalisisCognitivo.objects.get(estudiante=self.estudiante).areas_debiles,
            "Geometría",
        )
        self.bot.chat.assert_called_once()
        self.assertIn("academic_context", self.bot.chat.call_args.kwargs)

    def test_post_fallido_no_sincroniza_ni_pierde_respuesta_de_error(self):
        self.bot.chat.return_value = {
            "success": False,
            "error": "No hay modelo conectado",
            "chat_id": "uuid-fase8",
        }
        response = self.client.post(reverse("home"), {"prompt": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("No pudimos generar una respuesta", response.context["chat_error"])
        self.assertEqual(PerfilPedagogico.objects.count(), 0)
        self.assertEqual(AnalisisCognitivo.objects.count(), 0)

    def test_sincronizacion_es_transaccional_y_el_chat_no_falla_si_la_bd_falla(self):
        with patch(
            "Principal.services.tutor_profile_sync.set_AnalisisCognitivo",
            side_effect=RuntimeError("base fuera de servicio"),
        ):
            with self.assertLogs(
                "Principal.services.tutor_profile_sync", level="WARNING"
            ) as logs:
                response = self.client.post(reverse("home"), {"prompt": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["response"], "Practiquemos geometría")
        self.assertEqual(PerfilPedagogico.objects.count(), 0)
        self.assertEqual(AnalisisCognitivo.objects.count(), 0)
        self.assertEqual(NivelAprendizaje.objects.count(), 0)
        self.assertNotIn("Hola", " ".join(logs.output))

    def test_perfil_de_otro_usuario_no_se_sincroniza(self):
        self.bot.memory_manager.get_cognitive_profile.return_value = [
            {**self.perfil, "user_id": "999999"}
        ]
        response = self.client.post(reverse("home"), {"prompt": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PerfilPedagogico.objects.count(), 0)
        self.assertEqual(AnalisisCognitivo.objects.count(), 0)

    def test_sync_directo_sin_estudiante_no_escribe(self):
        self.assertFalse(sincronizar_perfil_academico(None, [self.perfil], str(self.user.pk)))
        self.assertEqual(PerfilPedagogico.objects.count(), 0)
