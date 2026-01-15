# ========================================================IMPORTS================================================================

import os

from typing import Optional

import chromadb

import uuid

from Principal.IA.prompts import get_extration_prompt

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.prompts import PromptTemplate

from Principal.IA.chains import get_chat_tittle_chain

from Principal.IA.LangGraph.graph_chatbot.states import parser_extract_memory

from langchain_chroma import Chroma

from Principal.IA.chains import chain_chatbot,chat_bot 

from Principal.IA.embeddings import get_embedding

import json 

from datetime import datetime

# ****************************************************IMPORTS*************************************************************

USER_DIR = "ProyectoDeGrado/DATABASES/USERS"

class ModernMemoryManager:

    def __init__(self,user_id: str):
        self.user_id = user_id
        self.user_dir = os.path.join(USER_DIR, self.user_id) 
        
        # Crear directorio del usuario si no existe
        if not os.path.exists(self.user_dir):
            os.makedirs(self.user_dir)

        # base de datos vectorial para memoria transversal 
        self.chroma_db_path = os.path.join(self.user_dir, "chroma_db")
        
        # sistema de extraccion inteligente de memoria transversal 
        self._init_extraction_system()
        
        # self.embedding_function = get_embedding("nomic-embed-text") # 
        self._init_vector_db()   

        # ruta de la base de datos langraph_database (reservado para persistencia LangGraph)
        self.langraph_db_path = os.path.join(self.user_dir, "langraph_database.db")
        
    # inicializar la base de datos vectorial de chroma
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
            try:
                self.collection = self.client.get_collection(f"memoria_{self.user_id}")
            except:
                self.collection = self.client.create_collection(f"memoria_{self.user_id}")
        except Exception as e:
            print(f"Error initializing vector ChromaDB: {e}")
            self.vectorstore = None
            self.collection = None

    # inicializar el sistema de extraccion de memoria inteligente
    def _init_extraction_system(self):      
        try:
            self.extraction_llm = chat_bot
            self.memory_parser = parser_extract_memory
            # self.extraction_template = get_extration_prompt(self.memory_parser)           
            self.extraction_template = PromptTemplate(
                template= """Analiza el siguiente mensaje del usuario y determina si contiene información importante que deba recordarse.
                          Categorías disponibles:
                          - personal: Nombre, edad, ubicación, familia, etc.
                          - profesional: Trabajo, empresa, proyectos, habilidades
                          - preferencias: Gustos, disgustos, preferencias personales
                          - hechos_importantes: Información relevante que debe recordarse
                          
                          Mensaje del usuario: "{user_message}"
                          
                          Si el mensaje contiene información importante, extrae UNA memoria (la más importante).
                          Si no contiene información relevante para recordar, responde con categoría "none".
                          
                          {format_instructions}""",
                input_variables=["user_message"],
                partial_variables={"format_instructions": self.memory_parser.get_format_instructions()}
                )
            
            self.extraction_chain = self.extraction_template | self.extraction_llm | self.memory_parser  
        except Exception as e:
            print(f"Error initializing extraction LLM: {e}")
            self.extraction_chain = None


    # ==========================================GESTION DE CHATS===============================================
     
    def get_user_chats(self):
        try:
            chats_meta_file = os.path.join(self.user_dir, "chats_meta.json")
            if not os.path.exists(chats_meta_file):
                return []
            
            # cargar meta datos 
            with open(chats_meta_file, "r", encoding="utf-8") as f:
                   chats_data = json.load(f)
            
            # ordenar los datos por ultima actualizacion 
            chats_data.sort(key=lambda x: x.get("last_updated", "") if isinstance(x,dict) else "", reverse=True)
            return chats_data
        except Exception as e:
            print(f"Error getting user chats: {e}")
            return [] 
    
    
    # guardar metadatos ligeros del chat 
    def save_chats_metadata(self,chats_data):
        try: 
            chats_meta_file = os.path.join(self.user_dir, "chats_meta.json")
            with open(chats_meta_file, "w", encoding="utf-8") as f:
                json.dump(chats_data, f, indent=2,ensure_ascii=False)
        except Exception as e:
            print(f"Error saving chats meta: {e}")
    

    # crear un nuevo chat
    def create_new_chat(self, first: str=""):
        chat_id = str(uuid.uuid4())
        
        #generar un titulo basado en el primer message 
        title= self.generate_chat_title(first) if first else "Nuevo Chat"
        
        # crear metadatos del chat 
        new_chat = {
            "chat_id": chat_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0
        }
        
        # cargar los chats existentes y agregar el nuevo chat
        chats_data = self.get_user_chats()
        chats_data.append(new_chat)
        self.save_chats_metadata(chats_data)
        
        return chat_id


    def update_chat_metadata(self, chat_id: str, title: str = None,increment_message_count: bool = False):
        
        chats_data = self.get_user_chats()
        for chat in chats_data:
            if chat["chat_id"] == chat_id:
                if title:
                    chat["title"] = title
                if increment_message_count:
                    chat["message_count"] = chat.get("message_count", 0) + 1
                chat["last_updated"] = datetime.now().isoformat()
                break
        else: 
            # si no existe chat crear entrada 
            if chat_id:
                new_chat = {
                    "chat_id": chat_id,
                    "title": title if title else "Nuevo Chat",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "message_count": 1 if increment_message_count else 0
                }
                chats_data.append(new_chat)
        self.save_chats_metadata(chats_data)
    
    # elimina un chat de los metadatos 
    def delete_chat(self, chat_id: str):
        try:
            chats_data = self.get_user_chats()
            chats_data = [chat for chat in chats_data if chat["chat_id"] != chat_id] 
            self.save_chats_metadata(chats_data)
            return True
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
    
    # obtiene la informacion de un chat especifico
    def get_chat_info(self, chat_id: str):
        try:
            chats_data = self.get_user_chats()
            for chat in chats_data:
                if chat["chat_id"] == chat_id:
                    return chat
            return None
        except Exception as e:
            print(f"Error getting chat info: {e}")
            return None
    
    # genera un titulo basado en elprimer mensage
    def generate_chat_title(self, first_message: str):
        try:
            if not self.extraction_chain:
                return first_message[:30] + "..." if len(first_message) > 30 else first_message 
            title_prompt = PromptTemplate(
                template="""Genera un título corto (máximo 4-5 palabras) para una conversación que comienza con este mensaje:              
                          "{message}"
                          
                          El título debe:
                          - Ser conciso y descriptivo
                          - Capturar el tema principal
                          - Ser apropiado para un historial de chat
                          - No incluir comillas
                          
                          Título:""",
            input_variables=["message"]
            ) 
            title_chain = title_prompt | self.extraction_llm      #get_chat_tittle_chain()
            response = title_chain.invoke({"message": first_message[:200]}) # verificar invoke y entrada de datos en la funcion en chains 
            title = response.content.strip().strip('"').strip("'")
            return title if len(title) < 50 else title[:50] + "..."
        except Exception as e:
            print(f"Error generating chat title: {e}")
            return first_message[:30] + "..." if len(first_message) > 30 else first_message
    
    # ******************************************GESTION DE CHATS*********************************************************************** 


    #=========================================================MEMORIA VECTORIAL ==============================================================================
    
    def save_memory_vectorial(self, text: str, metadata: Optional[dict] = None):

        if not self.collection:
            print("Vector store not initialized.")
            return ""
        try:
            # text = str(text or "")
            memory_id = str(uuid.uuid4())
            doc_metadata = metadata or {}
            doc_metadata.update({
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id
            })
    
            self.collection.add(
                documents=[text],
                ids=[memory_id],
                metadatas=[doc_metadata]                
            )
            return memory_id
        except Exception as e:
            print(f"Error saving memory to vector store: {e}")
            return ""
    
    #busca informacion relevanate en la memoria vectorial   
    def search_vector_memory(self, query: str, k: int = 5):
        if not self.collection:
            print("Vector store not initialized.")
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error searching vector memory: {e}")
            return []
    

    # obtiene todas las memorias vectoriales del usuario 
    def get_all_vector_memories(self):
        if not self.collection:
            print("Vector store not initialized.")
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
            print(f"Error retrieving all vector memories: {e}")
            return []
            
    # ***********************************************************MEMORIA VECTORIAL *****************************************************************************



    # ===========================================================EXTRACCION  INTELIGENTE=========================================================================

    # extrae memorias usando un llm 
    def extract_and_store_memories(self, user_message: str):
        if not self.extraction_chain:
            print("Extraction chain not initialized.")           
            return self._extract_memories_manual(user_message)
        try:
            extracted_memory = self.extraction_chain.invoke({"user_message": user_message})
            if extracted_memory.category.lower() != "none" and extracted_memory.importance >= 2: 
                memory_id = self.save_memory_vectorial(
                    extracted_memory.content,
                    {"category": extracted_memory.category,
                     "importance": extracted_memory.importance,
                     "original_message": user_message[:200]
                    }
                )
                return bool(memory_id)
            return False
        except Exception as e:
            print(f"Error extracting and storing memory: {e}")
            return self._extract_memories_manual(user_message)
    

    # extraccion manual de memoria basada en reglas simples
    def _extract_memories_manual(self, user_message: str) -> bool:
       message_lower = user_message.lower()
   
       memory_rules = [
            (["me llamo", "mi nombre es", "soy"], "personal", f"Info personal: {user_message}"),
            (["trabajo en", "trabajo como", "mi profesión"], "profesional", f"Info profesional: {user_message}"),
            (["me gusta", "me encanta", "prefiero", "odio"], "preferencias", f"Preferencia: {user_message}"),
            (["importante", "recuerda que", "no olvides"], "hechos_importantes", f"Hecho importante: {user_message}")
        ]
   
       for phrases, category, memory_text in memory_rules:
           if any(phrase in message_lower for phrase in phrases):
               memory_id = self.save_memory_vectorial(memory_text, {'category': category})
               return bool(memory_id)  
       return False

    # *************************************************************EXTRACCION  INTELIGENTE************************************************************************************************







# ==========================================================CLASE USER MANAGER ==============================================================================


class UserManager:

    @staticmethod
    def get_users():
        if not os.path.exists(USER_DIR):
            return []
        users=[]
        for item in os.listdir(USER_DIR):
            item_path = os.path.join(USER_DIR, item)
            if os.path.isdir(item_path):
                users.append(item)
        return sorted(users)


    @staticmethod
    def user_exists(user_id: str):
        user_path = os.path.join(USER_DIR, user_id)
        return os.path.exists(user_path) 
    
    @staticmethod
    def create_user(user_id: str):
        try:
            user_path = os.path.join(USER_DIR, user_id)
            os.makedirs(user_path, exist_ok=False)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
# **********************************************************CLASE USER MANAGER **********************************************************************************************************
