"""Perfiles cognitivos privados: análisis de historial y persistencia JSON."""
import logging
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate

from Principal.IA.llm import parser_CognitiveProfile

from .json_storage import load_json, save_json_atomic

logger = logging.getLogger(__name__)


class CognitiveProfileMixin:
    def _cognitive_profile_path(self):
        return Path(self.user_dir) / "cognitive_profile.json"

    def get_cognitive_profile(self):
        path = self._cognitive_profile_path()
        if not path.exists():
            return None
        try:
            return load_json(path)
        except (OSError, ValueError, TypeError):
            logger.error("cognitive_profile_read_failed", extra={"component": "profiles"})
            return None

    def save_cognitive_profile(self, profile: dict):
        if not isinstance(profile, dict):
            return False
        try:
            path = self._cognitive_profile_path()
            if path.exists():
                profiles = load_json(path)
                if isinstance(profiles, dict):
                    profiles = [profiles]
                elif not isinstance(profiles, list):
                    raise ValueError("Formato de perfiles inválido")
            else:
                profiles = []
            profile = dict(profile)
            profile["last_updated"] = datetime.now().isoformat()
            profiles.append(profile)
            save_json_atomic(path, profiles)
            return True
        except (OSError, ValueError, TypeError) as exc:
            logger.warning(
                "cognitive_profile_write_failed",
                extra={"component": "profiles", "error_type": type(exc).__name__},
            )
            return False

    def build_cognitive_profile(self, history: list, user_id: str):
        pairs = []
        current = {}
        for message in history:
            if isinstance(message, HumanMessage):
                current["user"] = message.content
            elif isinstance(message, AIMessage) and "user" in current:
                current["assistant"] = message.content
                pairs.append(current)
                current = {}
        profile = self.generate_cognitive_profile(pairs[-20:])
        if profile is None:
            return None
        now = datetime.now().isoformat()
        return {
            "chat_id": str(uuid.uuid4()),
            "user_id": user_id,
            "area": profile.area,
            "general_level": profile.general_level,
            "strong_areas": profile.strong_areas,
            "weak_areas": profile.weak_areas,
            "frequent_mistakes": profile.frequent_mistakes,
            "progress": profile.progress,
            "created_at": now,
            "last_update": now,
        }

    def generate_cognitive_profile(self, conversation_pairs: list):
        """Un modelo no disponible o un JSON incorrecto no crean perfiles falsos."""
        if not getattr(self, "extraction_chain", None):
            return None
        content = "Analiza la siguiente conversación y genera un perfil cognitivo.\n"
        for pair in conversation_pairs[-20:]:
            content += f"Usuario: {pair['user']}\nAsistente: {pair['assistant']}\n"
        try:
            prompt = PromptTemplate(
                template="""Genera un JSON válido para describir el perfil cognitivo.
{format_instructions}
Usa exclusivamente valores permitidos. Si no hay evidencia suficiente,
usa [] o null; detected_error solo cuando existan errores conceptuales
observables. No incluyas markdown.
Conversación: "{conversation_text}" """,
                input_variables=["conversation_text"],
                partial_variables={
                    "format_instructions": parser_CognitiveProfile.get_format_instructions()
                },
            )
            response = (prompt | self.extraction_llm).invoke(
                {"conversation_text": content}
            )
            return parser_CognitiveProfile.parse(response.content)
        except Exception as exc:
            logger.warning(
                "cognitive_profile_llm_failed",
                extra={"component": "ollama", "error_type": type(exc).__name__},
            )
            return None
