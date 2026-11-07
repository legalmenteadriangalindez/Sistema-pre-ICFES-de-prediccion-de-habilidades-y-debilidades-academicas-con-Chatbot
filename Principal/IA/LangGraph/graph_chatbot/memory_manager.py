"""API de memoria del tutor, compatible con importaciones anteriores.

Las responsabilidades están divididas en módulos internos. El almacenamiento
local y los nombres públicos de los métodos se mantienen para no invalidar los
chats ni perfiles ya guardados.
"""
import logging
import os

from django.conf import settings

from .conversation_store import ConversationStoreMixin
from .vector_memory import VectorMemoryMixin
from .memory_extraction import MemoryExtractionMixin
from .cognitive_profiles import CognitiveProfileMixin
from .external_resources import ExternalResourcesMixin

logger = logging.getLogger(__name__)
USER_DIR = settings.USER_DATA_ROOT


class ModernMemoryManager(
    ConversationStoreMixin,
    VectorMemoryMixin,
    MemoryExtractionMixin,
    CognitiveProfileMixin,
    ExternalResourcesMixin,
):
    """Facade por usuario: JSON de chats, Chroma, recuerdos y perfiles."""

    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        self.user_dir = os.path.join(USER_DIR, self.user_id)
        os.makedirs(self.user_dir, exist_ok=True)
        self.chroma_db_path = os.path.join(self.user_dir, "chroma_db")
        self._init_extraction_system()
        self._init_vector_db()
        # Reservado para el formato heredado: LangGraph usa langgraph_memory.db.
        self.langraph_db_path = os.path.join(self.user_dir, "langraph_database.db")


class UserManager:
    """Compatibilidad con gestión de directorios de usuarios existentes."""

    @staticmethod
    def get_users():
        if not os.path.exists(USER_DIR):
            return []
        return sorted(
            item for item in os.listdir(USER_DIR)
            if os.path.isdir(os.path.join(USER_DIR, item))
        )

    @staticmethod
    def user_exists(user_id: str):
        return os.path.exists(os.path.join(USER_DIR, str(user_id)))

    @staticmethod
    def create_user(user_id: str):
        try:
            os.makedirs(os.path.join(USER_DIR, str(user_id)), exist_ok=False)
            return True
        except (OSError, ValueError):
            logger.exception("No se pudo crear el directorio privado de usuario")
            return False
