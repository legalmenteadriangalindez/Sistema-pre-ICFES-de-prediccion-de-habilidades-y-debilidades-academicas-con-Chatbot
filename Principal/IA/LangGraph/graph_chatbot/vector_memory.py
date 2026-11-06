"""ChromaDB por usuario: guardar y consultar con el mismo modelo de embeddings."""
import logging
import uuid
from datetime import datetime
from typing import Optional

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorMemoryMixin:
    def _init_vector_db(self):
        self.vectorstore = None
        self.collection = None
        self.client = None
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            self.vectorstore = Chroma(
                collection_name=f"memoria_{self.user_id}",
                embedding_function=embeddings,
                persist_directory=self.chroma_db_path,
            )
            self.client = chromadb.PersistentClient(path=self.chroma_db_path)
            self.collection = self.client.get_or_create_collection(
                f"memoria_{self.user_id}"
            )
        except Exception as exc:
            logger.error(
                "chroma_initialization_failed",
                extra={"component": "chromadb", "error_type": type(exc).__name__},
            )
            self.vectorstore = None
            self.collection = None
            self.client = None

    def save_memory_vectorial(self, text: str, metadata: Optional[dict] = None):
        if not self.vectorstore and not self.collection:
            logger.warning("chroma_not_initialized", extra={"component": "chromadb"})
            return ""
        if not isinstance(text, str) or not text.strip():
            return ""
        try:
            memory_id = str(uuid.uuid4())
            doc_metadata = dict(metadata or {})
            doc_metadata.update({
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id,
            })
            if self.vectorstore:
                # Usar el embedding de HuggingFace para escritura y recuperación.
                self.vectorstore.add_texts(
                    texts=[text], metadatas=[doc_metadata], ids=[memory_id]
                )
            else:
                self.collection.add(
                    documents=[text], metadatas=[doc_metadata], ids=[memory_id]
                )
            return memory_id
        except Exception as exc:
            logger.warning(
                "chroma_write_failed",
                extra={"component": "chromadb", "error_type": type(exc).__name__},
            )
            return ""

    def search_vector_memory(self, query: str, k: int = 5):
        if not self.vectorstore and not self.collection:
            return []
        if not isinstance(query, str) or not query.strip():
            return []
        try:
            count = max(1, min(50, int(k)))
            if self.vectorstore:
                docs = self.vectorstore.similarity_search(query, k=count)
                return [doc.page_content for doc in docs]
            result = self.collection.query(query_texts=[query], n_results=count)
            return result["documents"][0] if result.get("documents") else []
        except Exception as exc:
            logger.warning(
                "chroma_search_failed",
                extra={"component": "chromadb", "error_type": type(exc).__name__},
            )
            return []

    def get_all_vector_memories(self):
        if not self.collection:
            return []
        try:
            result = self.collection.get()
            documents = result.get("documents") or []
            ids = result.get("ids") or []
            metadata = result.get("metadatas") or []
            return [
                {
                    "id": ids[index] if index < len(ids) else None,
                    "document": doc,
                    "metadata": metadata[index] if index < len(metadata) else {},
                }
                for index, doc in enumerate(documents)
            ]
        except Exception as exc:
            logger.warning(
                "chroma_list_failed",
                extra={"component": "chromadb", "error_type": type(exc).__name__},
            )
            return []
