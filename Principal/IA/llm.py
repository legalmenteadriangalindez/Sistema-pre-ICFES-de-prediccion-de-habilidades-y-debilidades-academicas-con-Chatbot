# ==========================================IMPORTACIONES================================================
import ollama #importación de la librería ollama

from langchain_community.chat_models import ChatOllama #importación de la clase Ollama desde langchain_community

from pydantic import BaseModel,Field # Libreria pydantic sirve para convertir string a a tipos de datos como json  Field sirve para ..

from langchain_core.output_parsers import PydanticOutputParser

from typing import List,Literal

#*******************************************IMPORTACIONES**********************************************************


llm = ChatOllama(model="llama3",temperature=0.1) #creación de una instancia del modelo LLM con el modelo "llama3" y una temperatura de 0.7 una temperatura baja es menos creativo una temperatura alta es mas creativo
chat_bot = ChatOllama(model="llama3:8b",base_url="http://127.0.0.1:11434",temperature=0) # ,num_predict=150
# chat_bot = ChatOllama(model="gemma3:4b-it-qat",temperature=0)
chat = ChatOllama(model="llama3:8b",base_url="http://127.0.0.1:11434",temperature=0)


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

