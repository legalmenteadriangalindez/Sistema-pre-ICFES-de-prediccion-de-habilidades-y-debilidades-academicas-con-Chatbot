# ==========================================IMPORTACIONES================================================
from .gestion_historial import guardar_historial

from Principal.IA.chains import chain_cuestionarios,chain_chatbot,chain_maateriales

from langchain_core.messages import AIMessage
# ******************************************IMPORTACIONES*************************************************

# ===========================================CHATBOT==============================================================

#------------chat bot--------------
def get_chain_chatbot(prompt: str):
   respuesta= chain_chatbot.invoke(prompt)
   if isinstance(respuesta,AIMessage) and isinstance(respuesta.content,str):
       return respuesta.content
   if isinstance(respuesta,AIMessage) and isinstance(respuesta.content,list):
       for msg in respuesta.content:
           if isinstance(msg,AIMessage):
               return msg.content
   if isinstance(respuesta,list):
       for msg in respuesta:
           if isinstance(msg,AIMessage):
               return msg.content  
   return str(respuesta.content)


# **********************************************************************************************************


# ===============================OBTENER CUESTIONARIOS=============================================================================

def get_respuesta(materia: str)-> dict: # metodo para obtener las respuestas en formato json 
    try:
        respuesta=chain_cuestionarios.invoke({"texto":materia})
        data = respuesta.model_dump()
        return {
            "contexto": data.get("contexto",""),
            "pregunta": data.get("pregunta",""),
            "opciones": {
                 "A": data.get("A",""),
                 "B": data.get("B",""),
                 "C": data.get("C",""),
                 "D": data.get("D","")
            },
            "respuesta_correcta": data.get("respuesta_correcta", "").strip().upper()
        }
    except Exception as e:
        print(e)
        return {
            "contexto": "error al generar contexto",
            "pregunta": "error al generar cuestionario",       
            "opciones":{
                "A": "",
                "B":"",
                "C": "",
                "D": ""
            },
             "respuesta_correcta": ""
         }
            


# ===============================OBTENER CUESTIONARIOS=============================================================================


#===================================GENERAR MATERIAL RECOMENDADO====================================================================================
    
def get_material_recomendado(contexto: str)-> dict: # metodo para obtener las respuestas en formato json 
    try:
        respuesta=chain_maateriales.invoke({
            "contexto":contexto
            })
        respuesta = respuesta.model_dump()
        return respuesta
    except Exception as e:
        print(e)
        return {
            "tematicas_recomendadas": []   
        }

 #*************************************GENERAR MATERIAL RECOMENDADO*********************************************************************************



# ================================================EXTRAER TEXTO DE IA =======================================================================
def extraer_texto_ai(respuesta):
    if isinstance(respuesta,str):
        return respuesta
    if isinstance(respuesta,AIMessage):
        return respuesta.content
    if isinstance(respuesta,list):
        for msg in respuesta: 
            if isinstance(msg,AIMessage):
               return msg.content 
    raise  ValueError("error al extraer el texto de la IA ")
# ***********************************************EXTRAER TEXTO CON IA ************************************************************************************


