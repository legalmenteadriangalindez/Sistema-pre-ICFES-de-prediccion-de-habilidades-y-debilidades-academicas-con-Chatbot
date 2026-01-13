#===================================IMPORTACIONES=============================================
from langchain_core.prompts import ChatPromptTemplate,SystemMessagePromptTemplate,HumanMessagePromptTemplate #importación de la clase PromptTemplate desde langchain.templates

from .llm import parser

from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import PydanticOutputParser
#*****************************************IMORTACIONES****************************************




#===================================PROMPT GENERAR CUESTIONARIOS=============================================

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

CHATBOT_SYSTEM= SystemMessagePromptTemplate.from_template(
    """Eres un asistente conversacional para un aplicativo que ayuda a mejorar las ruebas de estado ICFES
    REGLAS :
    - responde en español 
    - usa un tono profesional y amigable 
    - si no conoces la respuesta a la pregunta del usuario dile que no conoces la respuesta no inventes informacion
    - tu objetivo es ayudar al usuario a mejorar sus puntajes en los resultados de las pruebas de estado ICFES
    
"""
)

CHATBOT_HUMAN= HumanMessagePromptTemplate.from_template(
    """ {input}"""
)

CHATBOT_PROMPT= ChatPromptTemplate.from_messages([
    CHATBOT_SYSTEM,
    CHATBOT_HUMAN
])


def get_extration_prompt(memory_parser: PydanticOutputParser)-> PromptTemplate:
    CHATBOT_EXTRACTION_MEMORY= PromptTemplate(template="""Analiza la siguiente información del usuario:

                                                   {user_message}
                                                 
                                                   {format_instructions}
                                                 
                                                   Si NO existe información relevante para memoria a largo plazo,
                                                   responde exactamente con el siguiente JSON y nada más:
                                                 
                                                   {
                                                     "category": "none",
                                                     "content": "",
                                                     "importance": 1
                                                   }""",
                                     input_variables=["user_message"],
                                     partial_variables={"format_instructions": memory_parser.get_format_instructions()})
    return CHATBOT_EXTRACTION_MEMORY


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
#*****************************************PROMPT GENERAR CUESTIONARIOS****************************************




#===================================GENERAR MATERIAL=============================================

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

#*****************************************GENERAR MATERIAL****************************************




#==========================================MULTIQUERY PROMPT ===================================================

MULTI_QUERY_PROMPT=""" 

    Eres un asistente conversacional para un aplicativo que ayuda a mejorar las ruebas de estado ICFES
    tu tarea es generar multiples versiones de la consulta del usuario para recuperar informacion relevante 

    pregunta : {question}
    genera exactamente tres versiones de la pregunta del usuario una por linea sin numeracion ni viñetas  

"""


multiquery_retriver= ChatPromptTemplate.from_template(
    MULTI_QUERY_PROMPT
)
#******************************************MULTIQUERY PROMPT ***************************************************




#==========================================PROMPT RAG SYSTEM ===================================================

RAG_TEMPLATE=""" 
    Eres un asistente experto en pruebas de estado ICFES

    INSTRUCCION PRINCIPAL:
    rersponde unicamente basandote en los siguientes archivos,
    no agregues informacion fuera del contexto y los documentos 
    
    contexto:
    {context}

    pregunta : 
    {question}


    REGLAS :
    - responde en español 
    - usa un tono profesional y amigable 
    - has un resumen del contexto
    - si el contexto no tiene informacion suficiente dilo explicitamente
    - no inventes informacion 
    
    RESUMEN: 

"""

prompt_rag= ChatPromptTemplate.from_template(
    RAG_TEMPLATE
)
#******************************************PROMPT RAG SYSTEM ***************************************************