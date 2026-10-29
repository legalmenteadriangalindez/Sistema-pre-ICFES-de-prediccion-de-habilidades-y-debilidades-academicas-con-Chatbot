import os
from typing import List, Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")

llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.1)
chat_bot = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
chat = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)


# ==========================================RESPUESTAS ESTRUCTURADAS ==========================================================
class Cuestionarios(BaseModel):      # clase para convertir a formato determinado por ejemplo json 
    contexto: str = Field(description="contexto previo de la pregunta") 
    pregunta: str = Field(description="pregunta relacionada al contexto") 
    A: str = Field(description="posible respuesta")
    B: str = Field(description="posible respuesta")
    C: str = Field(description="posible respuesta")
    D: str = Field(description="posible respuesta")
    respuesta_correcta: str = Field(description="respuesta correcta(A|B|C|D)")

parser=PydanticOutputParser(pydantic_object=Cuestionarios)


class Diagnosticar_error(BaseModel):      # clase para convertir a formato determinado por ejemplo json 
    tipo_error: Literal["conceptual","procedimental","comprencion_lectora"]
    concepto_fallido: str 
    razon_fallo: str

parser_Diagnosticar=PydanticOutputParser(pydantic_object=Diagnosticar_error)

class Material_recomendado(BaseModel):      # clase para convertir a formato determinado por ejemplo json 
    tematicas_recomendadas: List[str]

parser_Material=PydanticOutputParser(pydantic_object=Material_recomendado)



# ==================================================================================================

class Cognitive_profile(BaseModel):
    area: Literal[
        "matematicas",
        "lectura_critica",
        "ciencias_naturales",
        "ciencias_sociales_y_ciudadanas",
        "ingles"
    ] = Field(description="Área principal evaluada")

    general_level: Literal[
        "basic",
        "intermediate",
        "advanced"
    ] = Field(description="Nivel general del usuario en el área")

    strong_areas: List[str] = Field(
        default_factory=list,
        description="Temas o habilidades que el usuario domina teniendo en cuenta la consulta que hizo"
    )

    weak_areas: List[str] = Field(
        default_factory=list,
        description="Temas que el usuario necesita reforzar para dominar el tema"
    )

    frequent_mistakes: List[str] = Field(
        default_factory=list,
        description="Errores recurrentes relacionados con la conversacion"
    )

    progress: List[str] = Field(
        default_factory=list,
        description="Temas donde se evidencia progreso"
    )

    score: int = Field(
        ge=1,
        le=5,
        description="Puntaje general entre 1 y 5"
    )

    detected_error: bool = Field(
        description="Indica si se detectaron errores conceptuales claros"
    )


parser_CognitiveProfile = PydanticOutputParser(
    pydantic_object=Cognitive_profile
)

