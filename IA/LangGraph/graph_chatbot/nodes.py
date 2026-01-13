# ====================================================IMPORTACIONES ===========================================================

from Principal.services.gestion_prompts import get_chain_chatbot

from Principal.IA.prompts import CHATBOT_PROMPT

from langchain_core.messages import SystemMessage,trim_messages # trim_messages sirve para la memoria deslizante 

from Principal.IA.chains import chain_chatbot

import uuid

from Principal.IA.vectorstore import vectorStoreChroma as vectorStore

# ****************************************************IMPORTACIONES ***************************************************************************



# =========================================NODO PARA GENERAR MEMORIA CHAT_BOTT ======================================================================

def chatbot_node(state):

    system_prompt = "eres un asistente que recuerda conversaciones y contextos previos "         #CHATBOT_PROMPT
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = chain_chatbot.invoke(messages)
    return  {"messages": [response]} 

# *************************************************************************************************************************************************


# =========================================NODO PARA GENERAR MEMORIA DESLIZANTE ======================================================================



trimmer = trim_messages(
    strategy="last",
    max_tokens=4,
    token_counter= len,
    start_on= "human",
    include_system=True
)

def chatbot_deslizante_node(state):
    trimmed_messages = trimmer.invoke(state["messages"])
    system_prompt = "eres un asistente que recuerda conversaciones y contextos previos "         #CHATBOT_PROMPT
    messages = [SystemMessage(content=system_prompt)] + trimmed_messages
    response = chain_chatbot.invoke(messages)
    return  {"messages": [response]} 

# *************************************************************************************************************************************************



# ===============================GUARDAR MEMORIA CON CHROMA (DB VECTORIAL)================================================================================

def save_memory(text):
    try:
        vectorStore.add_texts(
            texts=[text],
            metadatas=[{"source": "memoria_chatbot"}],
            ids= [str(uuid.uuid4())],
        )
        vectorStore.persist()
        print(f"guardado en memoria : {text}")
    except Exception as e :
        print(f"error : {e}")

def search_memory(consult,k=3):
    try : 
        result= vectorStore.similarity_search(
            consult,
            k=k
        )
        return  [doc.page_content for doc in result]       #result['documents'][0] if result['documents'] else []
    except:
        return []
    
def chat_vectorial_node(state):
    messages = state['messages']
    last_message = messages[-1].content if messages else ""

    memories = search_memory(last_message)

    system_prompt= "eres un asistente que recuerda informacion inportante"

    if memories: 
       system_prompt += "\n\ninformacion que recuerdas"
       for memory in memories:
           system_prompt += f"\n {memory}"
    messages_whit_system = [SystemMessage(content=system_prompt)] + messages
    response = chain_chatbot.invoke(messages_whit_system)


    message_lower = last_message.lower()
    if "me llamo " in message_lower:
        save_memory(f"el usuario se llama: {last_message}")
    elif any(frase in message_lower for frase in ["trabajo en "]):
        save_memory(f"trabajo del usuario: {last_message}")
    elif "me gusta" in message_lower or "me encanta" in message_lower:
        save_memory(f"favoritos : {last_message}")
    
    return {"messages": [response]}


# ********************************************************GUARDAR MEMORIA CON CHROMA (DB VECTORIAL)***********************************************************************