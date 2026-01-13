# ==========================================IMPORTACIONES================================================

from langchain_core.messages import AIMessage,HumanMessage, SystemMessage #importación de la clase PromptTemplate desde langchain.templates

from django.core.cache import cache  #importación de la clase cache desde django.core.cache

# *********************************************IMPORTACIONES********************************************************



# ============================================HISTORIAL DE MENSAGES============================================================

def guardar_historial(prompt: str):    
    historial = cache.get("chat_history") or []  #obtención del historial de mensajes almacenados en la caché
    mensaje = HumanMessage(content=prompt)  #creación de un mensaje 
    historial.append(mensaje)  #adición del mensaje al historial
    cache.set("chat_history", historial)  #almacenamiento del historial actualizado en la caché



def guardar_respuesta_ai(respuesta_ai):
    if not isinstance(respuesta_ai,str):
        raise TypeError(f"guardar respuesta ai solo acepta texto")
    historial = cache.get("chat_history") or []  #obtención del historial de mensajes almacenados en la caché
    mensaje = AIMessage(content=respuesta_ai)  #creación de un mensaje 
    historial.append(mensaje)  #adición del mensaje al historial
    cache.set("chat_history", historial)  #almacenamiento del historial actualizado en la caché
    return historial



def obtener_historial():    
    historial = cache.get("chat_history") or [] #obtención del historial de mensajes almacenados en la caché
    return historial



def eliminar_historial():
    cache.delete("chat_history")  #eliminación del historial de mensajes almacenados en la caché

def guardar_user(respuesta):
    historial = cache.get("chat_history") or []  #obtención del historial de mensajes almacenados en la caché
    historial.append(HumanMessage(content=respuesta))
    cache.set("chat_history",historial)

def guardar_ia(respuesta):
    if not isinstance(respuesta,str):
        raise TypeError(f"guardar ia recibio {type(respuesta)}")
    historial = cache.get("chat_history") or []  #obtención del historial de mensajes almacenados en la caché
    historial.append(AIMessage(content=respuesta))
    cache.set("chat_history",historial)

def procesar_historial(historial):
    historial_procesado = []
    for message in historial:
        if isinstance(message,HumanMessage):
            tipo="usuario"
            contenido = message.content
        elif isinstance(message,AIMessage):
            tipo="asistente"
            contenido = message.content
        elif isinstance(message,SystemMessage):
            tipo= "sistema"
            contenido = message.content
        else:
            tipo = "desconocido"
            contenido = str(message)
        historial_procesado.append({
            "tipo": tipo,
            "contenido": contenido
        })
    return historial_procesado

def verificar_tipo_de_usuario(historial):
  historial = cache.get("chat_history") or []  #obtención del historial de mensajes almacenados en la caché
  for message in historial:  #iteración sobre los mensajes almacenados en el historial de la caché
    if isinstance(message, HumanMessage):  #verificación si el mensaje es del tipo HumanMessage
        print(f"Usuario: {message.content}")  #impresión del contenido del mensaje del usuario
        rol = "usuario"
        print("====================ROL=================== \n" + rol)
    elif isinstance(message, AIMessage):  #verificación si el mensaje es del tipo AIMessage
        print(f"Asistente: {message.content}")  #impresión del contenido del mensaje del asistente
        rol = "asistente"
        print("====================ROL=================== \n" + rol)
    elif isinstance(message, SystemMessage):  #verificación si el mensaje es del tipo SystemMessage
        print(f"Sistema: {message.content}")  #impresión del contenido del mensaje del sistema
        rol = "sistema"
        print("====================ROL=================== \n" + rol)
    
# =========================================================================================================================