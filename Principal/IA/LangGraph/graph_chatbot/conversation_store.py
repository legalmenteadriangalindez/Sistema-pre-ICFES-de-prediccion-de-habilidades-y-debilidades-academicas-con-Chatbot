"""undefined"""
import json
import logging
import os
import uuid
from datetime import datetime
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class ConversationStoreMixin:
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
            logger.exception("getting user chats")
            return [] 
    
    
    # guardar metadatos ligeros del chat

    def save_chats_metadata(self,chats_data):
        try: 
            chats_meta_file = os.path.join(self.user_dir, "chats_meta.json")
            with open(chats_meta_file, "w", encoding="utf-8") as f:
                json.dump(chats_data, f, indent=2,ensure_ascii=False)
            return True
        except Exception as e:
            logger.exception("saving chats meta")
            return False
    

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
            return self.save_chats_metadata(chats_data)
        except Exception as e:
            logger.exception("deleting chat")
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
            logger.exception("getting chat info")
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
            logger.exception("generating chat title")
            return first_message[:30] + "..." if len(first_message) > 30 else first_message
