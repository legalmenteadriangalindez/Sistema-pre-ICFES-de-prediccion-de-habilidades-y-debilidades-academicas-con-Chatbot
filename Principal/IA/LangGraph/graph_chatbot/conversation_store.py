"""Metadatos de conversación: historial JSON y títulos de chat."""
import logging
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import PromptTemplate

from .json_storage import load_json, save_json_atomic

logger = logging.getLogger(__name__)


class ConversationStoreMixin:
    def _chat_metadata_path(self):
        return Path(self.user_dir) / "chats_meta.json"

    def get_user_chats(self):
        path = self._chat_metadata_path()
        if not path.exists():
            return []
        try:
            chats = load_json(path)
            if not isinstance(chats, list) or not all(isinstance(item, dict) for item in chats):
                raise ValueError("Formato de metadatos de chat inválido")
            return sorted(chats, key=lambda item: item.get("last_updated", ""), reverse=True)
        except (OSError, ValueError, TypeError):
            logger.error("chat_metadata_read_failed", extra={"component": "conversation_store"})
            return []

    def save_chats_metadata(self, chats_data):
        try:
            if not isinstance(chats_data, list):
                raise ValueError("Se esperaba una lista de conversaciones")
            save_json_atomic(self._chat_metadata_path(), chats_data)
            return True
        except (OSError, ValueError, TypeError):
            logger.error("chat_metadata_write_failed", extra={"component": "conversation_store"})
            return False

    def create_new_chat(self, first: str = ""):
        chat_id = str(uuid.uuid4())
        title = self.generate_chat_title(first) if first else "Nuevo Chat"
        now = datetime.now().isoformat()
        new_chat = {
            "chat_id": chat_id, "title": title, "created_at": now,
            "last_updated": now, "message_count": 0,
        }
        chats_data = self.get_user_chats()
        chats_data.append(new_chat)
        if not self.save_chats_metadata(chats_data):
            logger.error("chat_metadata_create_failed", extra={"component": "conversation_store"})
        return chat_id

    def update_chat_metadata(self, chat_id: str, title: str = None,
                             increment_message_count: bool = False):
        chats = self.get_user_chats()
        for chat in chats:
            if chat.get("chat_id") == chat_id:
                if title:
                    chat["title"] = title
                if increment_message_count:
                    chat["message_count"] = chat.get("message_count", 0) + 1
                chat["last_updated"] = datetime.now().isoformat()
                break
        else:
            if chat_id:
                now = datetime.now().isoformat()
                chats.append({
                    "chat_id": chat_id, "title": title or "Nuevo Chat",
                    "created_at": now, "last_updated": now,
                    "message_count": 1 if increment_message_count else 0,
                })
        self.save_chats_metadata(chats)

    def delete_chat(self, chat_id: str):
        try:
            chats = [chat for chat in self.get_user_chats() if chat.get("chat_id") != chat_id]
            return self.save_chats_metadata(chats)
        except (OSError, ValueError, TypeError):
            logger.error("chat_metadata_delete_failed", extra={"component": "conversation_store"})
            return False

    def get_chat_info(self, chat_id: str):
        return next(
            (chat for chat in self.get_user_chats() if chat.get("chat_id") == chat_id),
            None,
        )

    def generate_chat_title(self, first_message: str):
        """Ollama es opcional: sin servicio devolvemos un título legible."""
        fallback = first_message[:30] + "..." if len(first_message) > 30 else first_message
        if not getattr(self, "extraction_chain", None):
            return fallback
        try:
            prompt = PromptTemplate(
                template=(
                    "Genera un título corto (máximo 4-5 palabras) para una conversación "
                    'que comienza con este mensaje: "{message}"\n'
                    "El título debe ser conciso, descriptivo, sin comillas.\nTítulo:"
                ),
                input_variables=["message"],
            )
            response = (prompt | self.extraction_llm).invoke(
                {"message": first_message[:200]}
            )
            title = str(response.content).strip().strip('"').strip("'")
            return (title if len(title) < 50 else title[:50] + "...") or fallback
        except Exception as exc:
            logger.warning(
                "chat_title_llm_unavailable",
                extra={"component": "ollama", "error_type": type(exc).__name__},
            )
            return fallback
