"""Extracción de recuerdos: Ollama con alternativa local basada en reglas."""
import logging

from langchain_core.prompts import PromptTemplate

from Principal.IA.llm import chat_bot
from Principal.IA.LangGraph.graph_chatbot.states import parser_extract_memory

logger = logging.getLogger(__name__)


class MemoryExtractionMixin:
    def _init_extraction_system(self):
        self.extraction_llm = chat_bot
        self.memory_parser = parser_extract_memory
        self.extraction_chain = None
        try:
            self.extraction_template = PromptTemplate(
                template="""Analiza el siguiente mensaje y determina si contiene información
importante para recordar. Categorías: personal, profesional, preferencias,
hechos_importantes. Si no contiene información relevante, categoría "none".
Mensaje: "{user_message}"
Extrae UNA memoria como máximo.
{format_instructions}""",
                input_variables=["user_message"],
                partial_variables={
                    "format_instructions": self.memory_parser.get_format_instructions()
                },
            )
            self.extraction_chain = (
                self.extraction_template | self.extraction_llm | self.memory_parser
            )
        except Exception as exc:
            logger.warning(
                "memory_extractor_init_failed",
                extra={"component": "ollama", "error_type": type(exc).__name__},
            )

    def extract_and_store_memories(self, user_message: str):
        if not isinstance(user_message, str) or not user_message.strip():
            return False
        if self.extraction_chain is None:
            return self._extract_memories_manual(user_message)
        try:
            extracted = self.extraction_chain.invoke({"user_message": user_message})
            if extracted.category.lower() == "none" or extracted.importance < 2:
                return False
            return bool(self.save_memory_vectorial(
                extracted.content,
                {
                    "category": extracted.category,
                    "importance": extracted.importance,
                    "original_message": user_message[:200],
                },
            ))
        except Exception as exc:
            logger.warning(
                "memory_extraction_llm_failed",
                extra={"component": "ollama", "error_type": type(exc).__name__},
            )
            return self._extract_memories_manual(user_message)

    def _extract_memories_manual(self, user_message: str) -> bool:
        message = user_message.lower()
        rules = [
            (["me llamo", "mi nombre es", "soy"], "personal", "Info personal"),
            (["trabajo en", "trabajo como", "mi profesión"], "profesional", "Info profesional"),
            (["me gusta", "me encanta", "prefiero", "odio"], "preferencias", "Preferencia"),
            (["importante", "recuerda que", "no olvides"], "hechos_importantes", "Hecho importante"),
        ]
        for phrases, category, prefix in rules:
            if any(phrase in message for phrase in phrases):
                return bool(self.save_memory_vectorial(
                    f"{prefix}: {user_message}", {"category": category}
                ))
        return False
