"""undefined"""
import json
import logging
import os
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from Principal.IA.llm import parser_CognitiveProfile

logger = logging.getLogger(__name__)


class CognitiveProfileMixin:
    def get_cognitive_profile(self):
        path = os.path.join(self.user_dir, "cognitive_profile.json")
    
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            logger.exception("No se pudo leer el perfil cognitivo")
            return None

    def save_cognitive_profile(self, profile: dict):
        profile["last_updated"] = datetime.now().isoformat()
        path = os.path.join(self.user_dir, "cognitive_profile.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
              profiles = json.load(f)
            if not isinstance(profiles, list):
                profiles = []
        else:
            profiles = []
        
        profiles.append(profile)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)

    def build_cognitive_profile(self, history: list,user_id:str):
        conversation_pairs = []
        temp_pair = {}
        for msg in history:
            if isinstance(msg, HumanMessage):
                temp_pair["user"] = msg.content
            elif isinstance(msg, AIMessage) and "user" in temp_pair:
                temp_pair["assistant"] = msg.content
                conversation_pairs.append(temp_pair)
                temp_pair = {}
    
        # limitar a últimos 20 pares
        conversation_pairs = conversation_pairs[-20:]
        cognitive_profile_id = str(uuid.uuid4())
        cognitive_profile = self.generate_cognitive_profile(conversation_pairs)
        if cognitive_profile is  None :
            return None
        
        return {
        "chat_id": cognitive_profile_id,
        "user_id": user_id,
        "area": cognitive_profile.area,
        "general_level": cognitive_profile.general_level,
        "strong_areas": cognitive_profile.strong_areas,
        "weak_areas" : cognitive_profile.weak_areas,
        "frequent_mistakes": cognitive_profile.frequent_mistakes,
        "progress": cognitive_profile.progress,
        "created_at": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat(),
        }

  
    
    # genera un titulo basado en elprimer mensage

    def generate_cognitive_profile(self, conversation_pairs: list):
        try:
            prompt_content = "analiza la siguiente conversacion y genera un perfil cognitivo\n"
            for i, pair in enumerate(conversation_pairs[-20:]):  # últimos 20 pares
                prompt_content += f"Usuario: {pair['user']}\nAsistente: {pair['assistant']}\n"
            if not self.extraction_chain:
                return None 
            cognitive_profile_prompt = PromptTemplate(
                template="""Genera un json valido basandote en la siguiente conversacion.
                          {format_instructions}
                          no incluyas explicaciones texto adicional ni markdown.              
                          conversacion :"{conversation_text}"
                          Reglas obligatorias:
                          - Usa solo los valores permitidos.
                          - Si no hay información suficiente para algún campo, devuelve un array vacío [] o null.
                          - detected_error debe ser true SOLO si hay errores conceptuales claros.
                          - El JSON debe ser perfectamente parseable por json.loads().
                          """,
            input_variables=["conversation_text"],
            partial_variables={
                "format_instructions": parser_CognitiveProfile.get_format_instructions()
             }
            ) 
            cognitive_profile_chain = cognitive_profile_prompt | self.extraction_llm      
            response = cognitive_profile_chain.invoke({"conversation_text": prompt_content  }) 
            try: 
                result = parser_CognitiveProfile.parse(response.content)
                return result
            except Exception as e : 
                logger.exception("La respuesta de Ollama no cumple el esquema del perfil")
                return None
        except Exception as e:
            logger.exception("generating cognitive profile")
            return None
