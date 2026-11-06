"""undefined"""
import logging
import uuid
from datetime import datetime
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorMemoryMixin:
    def _init_vector_db(self):
        try:
            self.vectorstore = Chroma(
                collection_name=f"memoria_{self.user_id}",
                embedding_function= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",model_kwargs={"device": "cpu"},
                                                          encode_kwargs={"normalize_embeddings": True}
                                                         ), 
                persist_directory=self.chroma_db_path
            )
            self.client = chromadb.PersistentClient(path=self.chroma_db_path)
            self.collection = self.client.get_or_create_collection(f"memoria_{self.user_id}")
        except Exception as e:
            logger.exception("initializing vector ChromaDB")
            self.vectorstore = None
            self.collection = None
            self.client = None

    # inicializar el sistema de extraccion de memoria inteligente

    def save_memory_vectorial(self, text: str, metadata: Optional[dict] = None):

        if not self.collection and not self.vectorstore:
            logger.warning("Almacenamiento vectorial no inicializado")
            return ""
        try:
            # text = str(text or "")
            memory_id = str(uuid.uuid4())
            doc_metadata = dict(metadata or {})
            doc_metadata.update({
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id
            })
    
            if self.vectorstore:
                self.vectorstore.add_texts(texts=[text], metadatas=[doc_metadata], ids=[memory_id])
            else:
                self.collection.add(documents=[text], ids=[memory_id], metadatas=[doc_metadata])
            return memory_id
        except Exception as e:
            logger.exception("saving memory to vector store")
            return ""
    
    #busca informacion relevanate en la memoria vectorial

    def search_vector_memory(self, query: str, k: int = 5):
        if not self.collection:
            logger.warning("Almacenamiento vectorial no inicializado")
            return []
        try:
            if self.vectorstore:
                return [item.page_content for item in self.vectorstore.similarity_search(query, k=k)]
            results = self.collection.query(query_texts=[query], n_results=k)
            return results["documents"][0] if results.get("documents") else []
        except Exception as e:
            logger.exception("searching vector memory")
            return []
    

    # obtiene todas las memorias vectoriales del usuario

    def get_all_vector_memories(self):
        if not self.collection:
            logger.warning("Almacenamiento vectorial no inicializado")
            return []
        try:
            results = self.collection.get()
            memories= []
            if not results.get('documents'):
                return []
            if results['documents'] :
                for i, doc in enumerate(results['documents']):
                    memory= {
                        'id': results['ids'][i],
                        'document': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {}
                    }
                    memories.append(memory)
            return memories               
        except Exception as e:
            logger.exception("retrieving all vector memories")
            return []
