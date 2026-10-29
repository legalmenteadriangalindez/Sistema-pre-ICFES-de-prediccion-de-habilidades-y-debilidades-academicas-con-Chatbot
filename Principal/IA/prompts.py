"""Prompts activos de cuestionarios, materiales y títulos de chat."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

GENERAR_CUESTIONARIOS_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system","""
    eres un generador automatico de textos academicos.
     
    INSTRUCCIONES OBLIGATORIAS: 
     
    -responde EXCLUSIVAMENTE con un objeto JSON valido.
    -genera un contexto para la pregunta que sea muy largo.
    -NO incluyas explicaciones,saludos ni texto adicional.
    - NO uses markdown ni comillas triples.
    - si no puedes cumplir con esta taresa responde con un JSON vacio.
    {format_instructions} """),
    ("human","{texto}")
])

#*****************************************PROMPT GENERAR CUESTIONARIOS****************************************




#===================================PROMPT GENERAR CUESTIONARIOS=============================================

def get_chat_tittle_prompt()->PromptTemplate:
    return PromptTemplate(
                template="""Genera un titulo conciso y descriptivo para la siguiente conversacion del usuario: {user_message}""",
                input_variables=["user_message"]
            )

def get_system_prompt(context:str)->str:
    return (
        "Eres un asistente de IA amigable y servicial. "
        "Utiliza el contexto proporcionado para responder "
        "de manera precisa y concisa.\n\n"
        f"{context}"
    )

GENERAR_MATERIAL_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system","""
     Eres un generador de JSON.
 
     Tu tarea es recomendar los temas académicos que el estudiante debe estudiar
     para poder responder correctamente preguntas como la presentada en el contexto.
     
     Reglas obligatorias:
    - Basa la recomendación únicamente en el contexto.
    - Recomienda contenidos académicos concretos (temas de estudio).
    - No incluyas explicaciones, ejemplos ni texto adicional.
    - La lista de temas no debe estar vacía.
    - Responde exclusivamente en formato JSON válido.
    
    Formato de salida obligatorio:
     
    {{
     "tematicas_recomendadas":[
     "tema_1",
     "tema_2",
     "tema_3"
     ]
    }}
     
    {format_instructions}"""),
    ("human","""
    Contexto:
    {contexto}
    
    """)
])
