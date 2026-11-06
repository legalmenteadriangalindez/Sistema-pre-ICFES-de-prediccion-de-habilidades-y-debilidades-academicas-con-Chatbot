"""Regresiones de memoria del tutor sin conectarse a Ollama/Chroma reales."""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from langchain_core.messages import AIMessage, HumanMessage

from Principal.IA.LangGraph.graph_chatbot.chatbot import ModernChatbot
from Principal.IA.LangGraph.graph_chatbot.memory_manager import (
    ModernMemoryManager, UserManager,
)
from Principal.IA.LangGraph.graph_chatbot.json_storage import save_json_atomic


class MemoriaModularTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manager = ModernMemoryManager.__new__(ModernMemoryManager)
        self.manager.user_id = "demo1"
        self.manager.user_dir = self.tmp.name
        self.manager.chroma_db_path = str(Path(self.tmp.name) / "chroma_db")
        self.manager.collection = None
        self.manager.vectorstore = None
        self.manager.extraction_chain = None
        self.manager.extraction_llm = MagicMock()

    def test_api_publica_se_mantiene(self):
        for name in (
            "get_user_chats", "save_chats_metadata", "create_new_chat",
            "update_chat_metadata", "delete_chat", "get_chat_info",
            "generate_chat_title", "save_memory_vectorial",
            "search_vector_memory", "get_all_vector_memories",
            "extract_and_store_memories", "get_cognitive_profile",
            "save_cognitive_profile", "build_cognitive_profile",
            "generate_cognitive_profile",
        ):
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(self.manager, name)))

    def test_lectura_escritura_y_borrado_de_conversaciones_sin_migracion(self):
        chat_id = self.manager.create_new_chat()
        self.assertEqual(self.manager.get_chat_info(chat_id)["title"], "Nuevo Chat")
        self.assertTrue((Path(self.tmp.name) / "chats_meta.json").exists())
        self.manager.update_chat_metadata(chat_id, "Matemáticas", True)
        chat = self.manager.get_chat_info(chat_id)
        self.assertEqual(chat["title"], "Matemáticas")
        self.assertEqual(chat["message_count"], 1)
        self.assertEqual(len(self.manager.get_user_chats()), 1)
        self.assertTrue(self.manager.delete_chat(chat_id))
        self.assertEqual(self.manager.get_user_chats(), [])

    def test_guardado_atomico_no_destrue_archivo_ante_json_invalido(self):
        path = Path(self.tmp.name) / "chats_meta.json"
        path.write_text('[{"chat_id":"conservado"}]', encoding="utf-8")
        with self.assertRaises(TypeError):
            save_json_atomic(path, {"invalido": {1, 2}})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[0]["chat_id"], "conservado")
        self.assertEqual(list(Path(self.tmp.name).glob("*.tmp")), [])

    def test_fallo_de_escritura_devuelve_false_sin_borrar_historial(self):
        path = Path(self.tmp.name) / "chats_meta.json"
        path.write_text('[{"chat_id":"existente"}]', encoding="utf-8")
        with patch("Principal.IA.LangGraph.graph_chatbot.conversation_store.save_json_atomic",
                   side_effect=OSError("disco ocupado")):
            with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.conversation_store", level="ERROR"):
                self.assertFalse(self.manager.save_chats_metadata([]))
        self.assertEqual(self.manager.get_chat_info("existente")["chat_id"], "existente")

    def test_metadata_corrupta_no_se_sobrescribe_al_crear_chat(self):
        path = Path(self.tmp.name) / "chats_meta.json"
        path.write_text('{datos dañados', encoding="utf-8")
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.conversation_store", level="ERROR"):
            self.assertFalse(self.manager.save_chats_metadata([]))
        self.assertEqual(path.read_text(encoding="utf-8"), '{datos dañados')

    def test_perfiles_anteriores_siguen_en_formato_json_lista(self):
        self.assertTrue(self.manager.save_cognitive_profile({"area": "lectura"}))
        self.assertTrue(self.manager.save_cognitive_profile({"area": "matematicas"}))
        records = self.manager.get_cognitive_profile()
        self.assertEqual([r["area"] for r in records], ["lectura", "matematicas"])
        self.assertTrue(all("last_updated" in r for r in records))

    def test_json_de_perfil_corrupto_no_se_sobrescribe(self):
        path = Path(self.tmp.name) / "cognitive_profile.json"
        path.write_text('{"archivo":', encoding="utf-8")
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.cognitive_profiles", level="ERROR"):
            self.assertIsNone(self.manager.get_cognitive_profile())
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.cognitive_profiles", level="WARNING"):
            self.assertFalse(self.manager.save_cognitive_profile({"area": "ciencias"}))
        self.assertEqual(path.read_text(encoding="utf-8"), '{"archivo":')

    def test_chromadb_indisponible_no_impide_iniciar_fachada(self):
        with patch("Principal.IA.LangGraph.graph_chatbot.vector_memory.HuggingFaceEmbeddings",
                   return_value=MagicMock()):
            with patch("Principal.IA.LangGraph.graph_chatbot.vector_memory.Chroma",
                       side_effect=OSError("almacenamiento vectorial caído")):
                with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.vector_memory", level="ERROR"):
                    self.manager._init_vector_db()
        self.assertIsNone(self.manager.collection)
        self.assertIsNone(self.manager.vectorstore)
        self.assertEqual(self.manager.search_vector_memory("álgebra"), [])
        self.assertEqual(self.manager.get_all_vector_memories(), [])
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.vector_memory", level="WARNING"):
            self.assertEqual(self.manager.save_memory_vectorial("álgebra"), "")

    def test_chroma_reutiliza_embedding_para_guardar_y_buscar(self):
        self.manager.collection = MagicMock()
        self.manager.vectorstore = MagicMock()
        self.manager.vectorstore.similarity_search.return_value = [
            MagicMock(page_content="Me cuesta álgebra")
        ]
        metadata = {"category": "preferencias"}
        mem_id = self.manager.save_memory_vectorial("Me cuesta álgebra", metadata)
        self.assertTrue(mem_id)
        kwargs = self.manager.vectorstore.add_texts.call_args.kwargs
        self.assertEqual(kwargs["texts"], ["Me cuesta álgebra"])
        self.assertEqual(kwargs["metadatas"][0]["memory_id"], mem_id)
        self.assertEqual(kwargs["metadatas"][0]["user_id"], "demo1")
        self.assertNotIn("memory_id", metadata)
        self.assertEqual(self.manager.search_vector_memory("álgebra"), ["Me cuesta álgebra"])
        self.manager.vectorstore.similarity_search.assert_called_once_with("álgebra", k=5)

    def test_errores_de_chroma_en_lectura_y_escritura_devuelven_resultados_vacios(self):
        self.manager.collection = MagicMock()
        self.manager.vectorstore = MagicMock()
        self.manager.vectorstore.add_texts.side_effect = RuntimeError("Chroma write")
        self.manager.vectorstore.similarity_search.side_effect = RuntimeError("Chroma read")
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.vector_memory", level="WARNING"):
            self.assertEqual(self.manager.save_memory_vectorial("texto"), "")
            self.assertEqual(self.manager.search_vector_memory("texto"), [])

    def test_chroma_lista_memorias_con_el_esquema_anterior(self):
        self.manager.collection = MagicMock()
        self.manager.collection.get.return_value = {
            "ids": ["m1"], "documents": ["Recuerdo"],
            "metadatas": [{"category": "personal"}],
        }
        self.assertEqual(self.manager.get_all_vector_memories(), [
            {"id": "m1", "document": "Recuerdo", "metadata": {"category": "personal"}}
        ])

    def test_ollama_falla_en_titulo_y_usa_texto_original(self):
        first = "Necesito estudiar ecuaciones lineales para mi examen"
        self.manager.extraction_chain = object()
        with patch("Principal.IA.LangGraph.graph_chatbot.conversation_store.PromptTemplate") as prompt:
            prompt.return_value.__or__.return_value.invoke.side_effect = ConnectionError("modelo no encontrado")
            with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.conversation_store", level="WARNING") as logs:
                title = self.manager.generate_chat_title(first)
        self.assertEqual(title, first[:30] + "...")
        self.assertNotIn(first, " ".join(logs.output))

    def test_ollama_falla_en_extraccion_y_activa_reglas_locales(self):
        self.manager.extraction_chain = MagicMock()
        self.manager.extraction_chain.invoke.side_effect = ConnectionError("Ollama apagado")
        self.manager.save_memory_vectorial = MagicMock(return_value="memoria-1")
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.memory_extraction", level="WARNING") as logs:
            ok = self.manager.extract_and_store_memories("Me gusta aprender ciencias")
        self.assertTrue(ok)
        self.assertEqual(self.manager.save_memory_vectorial.call_args.args[1]["category"], "preferencias")
        self.assertNotIn("Me gusta aprender ciencias", " ".join(logs.output))

    def test_ollama_responde_json_invalido_y_no_se_inventa_perfil(self):
        self.manager.extraction_chain = object()
        with patch("Principal.IA.LangGraph.graph_chatbot.cognitive_profiles.PromptTemplate") as prompt:
            prompt.return_value.__or__.return_value.invoke.return_value = MagicMock(content="mal json")
            with patch("Principal.IA.LangGraph.graph_chatbot.cognitive_profiles.parser_CognitiveProfile") as parser:
                parser.parse.side_effect = ValueError("Formato inválido")
                with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.cognitive_profiles", level="WARNING"):
                    result = self.manager.generate_cognitive_profile([{"user": "texto", "assistant": "respuesta"}])
        self.assertIsNone(result)

    def test_construir_perfil_sin_ollama_retorna_none(self):
        self.manager.extraction_chain = None
        result = self.manager.build_cognitive_profile(
            [HumanMessage(content="Matemáticas"), AIMessage(content="Vamos a estudiar")], "demo1"
        )
        self.assertIsNone(result)

    def test_fallo_de_perfil_en_grafo_no_interrumpe_los_mensajes(self):
        bot = ModernChatbot.__new__(ModernChatbot)
        bot.user_id = "demo1"
        bot.memory_manager = MagicMock()
        bot.memory_manager.user_dir = self.tmp.name
        bot.memory_manager.build_cognitive_profile.side_effect = ConnectionError("Ollama caído")
        with patch("Principal.IA.LangGraph.graph_chatbot.chatbot.StateGraph") as graph:
            with patch("Principal.IA.LangGraph.graph_chatbot.chatbot.SqliteSaver"):
                with patch("Principal.IA.LangGraph.graph_chatbot.chatbot.sqlite3.connect"):
                    bot._create_app_graph()
        callback = next(
            call.args[1] for call in graph.return_value.add_node.call_args_list
            if call.args[0] == "profile_cognitive"
        )
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.chatbot", level="WARNING"):
            self.assertEqual(callback({"messages": [HumanMessage(content="hola")]}), {})
        bot.memory_manager.save_cognitive_profile.assert_not_called()

    def test_chat_sin_ollama_devuelve_error_controlado_sin_revelar_prompt(self):
        bot = ModernChatbot.__new__(ModernChatbot)
        bot.user_id = "demo1"
        bot.memory_manager = MagicMock()
        bot.memory_manager.get_chat_info.return_value = {"chat_id": "c1", "title": "Tema"}
        bot.app_graph = MagicMock()
        bot.app_graph.invoke.side_effect = ConnectionError("prompt privado /llm/endpoint")
        with self.assertLogs("Principal.IA.LangGraph.graph_chatbot.chatbot", level="WARNING") as logs:
            answer = bot.chat("Pregunta personal", chat_id="c1")
        self.assertFalse(answer["success"])
        self.assertEqual(answer["chat_id"], "c1")
        self.assertIn("Ollama", answer["error"])
        self.assertNotIn("prompt privado", answer["error"])
        self.assertNotIn("Pregunta personal", " ".join(logs.output))
