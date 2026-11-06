"""undefined"""
import logging
from langchain_core.prompts import PromptTemplate
from Principal.IA.llm import chat_bot
from Principal.IA.LangGraph.graph_chatbot.states import parser_extract_memory

logger = logging.getLogger(__name__)


class MemoryExtractionMixin:
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
            logger.exception("initializing extraction LLM")
            self.extraction_chain = None

    def extract_and_store_memories(self, user_message: str):
        if not self.extraction_chain:
            logger.warning("Extracción LLM no inicializada; se usa alternativa por reglas")           
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
            logger.exception("extracting and storing memory")
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
