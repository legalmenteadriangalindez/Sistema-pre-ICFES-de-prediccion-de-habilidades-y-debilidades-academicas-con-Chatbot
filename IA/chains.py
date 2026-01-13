# ==========================================IMPORTACIONES================================================
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables import RunnablePassthrough

from langchain_core.output_parsers import StrOutputParser

from .llm import chat_bot,parser,llm,parser_Material

from .prompts import GENERAR_CUESTIONARIOS_TEMPLATE,GENERAR_MATERIAL_TEMPLATE,CHATBOT_PROMPT,prompt_rag,get_chat_tittle_prompt,get_system_prompt


# ********************************************IMPORTACIONES********************************************************



# ========================================== CHATBOT=========================================================

chain_chatbot = CHATBOT_PROMPT | chat_bot

def get_chat_tittle_chain():
   prompt = get_chat_tittle_prompt()
   llm = chat_bot

   return prompt | llm 

def get_response_generation_chain(context:str):
   prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt(context)),
        MessagesPlaceholder(variable_name="messages")
    ])
   return prompt | chat_bot
# ***************************************** CHATBOT***********************************************


# ========================================CUESTIOARIOS ============================================
cuestionario_prompt = GENERAR_CUESTIONARIOS_TEMPLATE.partial(format_instructions=parser.get_format_instructions())

chain_cuestionarios = cuestionario_prompt | llm | parser

# *******************************************CUESTIONARIOS******************************************



# ========================================GENERAR_MATERIAL ============================================
materiales_prompt = GENERAR_MATERIAL_TEMPLATE.partial(format_instructions=parser_Material.get_format_instructions())

chain_maateriales = materiales_prompt | llm | parser_Material

# *******************************************GENERAR_MATERIAL******************************************


# ========================================RAG CHAIN ============================================

def get_chain_rag(retriever,prompt,llm):
   return  (   
      {
       "context": retriever,
       "question": RunnablePassthrough() 
      }
      | prompt 
      | llm 
      | StrOutputParser()
  
      )


# ****************************************RAG CHAIN**********************************************




# =============================================RUNNEABLES ANALISIS DE SENTIMIENTOS RESEÑAS =========================================================

# def procesar_textos(text): # funcion para limitar el texto hasta 500 caracteres
#     if isinstance(text,dict):
#         text = text.get("prompt") or text.get("texto") or text.get("nombre") or ""
#     return str(text).strip()[:500]

# procesador=RunnableLambda(procesar_textos)  # convierte la funcion procesar_textos a runneable 


# def get_resumen(text):   # funcion para generar el resumen 
#     prompt=f"genera un resumen de el siguiente texto en una sola frase no respondas nada solo haz un resumen texto : {text}"
#     respuesta= llm.invoke(prompt)
#     return respuesta


# resumen_branch= RunnableLambda(get_resumen) # convierte la funcion get_resumen en un RUnnable


# def analizar_sentimiento(text):  # funcion para nalizar el sentimiento
#     prompt= f'''analiza el sentimiento del siguiente texto.responde unicamente en formato Json valido 
#     {{"sentimiento": "bueno|malo|neutro",
#       "razón": justificacion breve }} : {text}'''
#     respuestas = llm.invoke(prompt)
#     try:
#         return json.loads(respuestas)
#     except json.JSONDecodeError:
#         return {"sentimiento": "neutro", "razon": "error de analisis" }
    

# sentimiento_branch=RunnableLambda(analizar_sentimiento) # convierte la funcion analizar sentimiento en Runnable

# def unir_resultados(data):      # funcion para unir "merge" resultados
#     return {"resumen": data["resumen"],
#             "sentimiento": data["sentimiento_data"]["sentimiento"],
#             "razon": data["sentimiento_data"].get("razón") or  data["sentimiento_data"].get("razon")
#             }


# def convertir_Json_Valido(texto):
#     json_valido=json.dumps(texto,ensure_ascii=False,indent=2) # convertir Json a json valido
#     return json_valido


# unir = RunnableLambda(unir_resultados)  # convierte la funcion unir resultado en Runnable 
    
# analisis_paralelo = RunnableParallel({
#     "resumen": resumen_branch,
#     "sentimiento_data": sentimiento_branch
# })


# # cadena "chain" completa 
# chain= procesador | analisis_paralelo | unir



# def get_respuestas(reseñas):
#    return chain.batch(reseñas)


# ****************************************************RUNNEABLES ANALISIS DE SENTIMIENTOS RESEÑAS ****************************************************




#===========================================RUNNEABLES GENERAR CUESTONARIOS==================================================================

# def generar_cuestionarios(text):
#     prompt = f'''genera un cuestionario tipo icfes en español.
#     responde unicamente en formato Json valido sin texto adicional.
#     no generes listas ni multiples objetos
#     estructura obligatoria:
#     {{"pregunta": "",
#     "A": "",
#     "B": "",
#     "C": "",
#     "D": ""}} tema: {text} '''
#     respuesta= llm.invoke(prompt)
#     # respuesta_jason=convertir_Json_Valido(respuesta)
#     try:
#         return json.loads(respuesta)
#     except json.JSONDecodeError:
#         return {
#             "pregunta": "error al generar cuestionario",
#             "A": "",
#             "B": "",
#             "C": "",
#             "D": ""
#         }
    

# cuestionario_branch= RunnableLambda(generar_cuestionarios) # convertir la funcion generar cuestionario en Runneable

# chain_cuestionarios= procesador | cuestionario_branch


# def get_Cuestonarios(text):
#      return chain_cuestionarios.invoke(text)


# Few-shot examples para análisis de sentimientos

#**************************************************RUNNEABLES GENERAR CUESTONARIOS****************************************************




