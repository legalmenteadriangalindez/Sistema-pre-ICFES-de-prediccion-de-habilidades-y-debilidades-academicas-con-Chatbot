#===================================================IMPORTACIONES=============================================

from langchain_core.messages import SystemMessage,HumanMessage


from langgraph.graph import StateGraph,MessagesState,START

from langgraph.checkpoint.sqlite import SqliteSaver

# from langgraph.checkpoint.memory import MemorySaver

# from langgraph.checkpoint.postgres import PostgresSaver

from .nodes import chatbot_node,chatbot_deslizante_node,chat_vectorial_node,vectorStore

import sqlite3 


#****************************************************IMORTACIONES********************************************************





# ======================================================CONFIGURACION DE LA BASE DE DATOS (Chroma o FAISS )=======================================================================



# client = Chroma.PersistentClient(path=CHROMA_DB)

# collection = client.get_collection("memory_chat")

conn = sqlite3.connect("historial_db.sqlite3",check_same_thread=False)

memory = SqliteSaver(conn)

# *********************************************************CONFIGURACION DE LA BASE DE DATOS (Chroma o FAISS )*********************************************************************




#==============================================================GRAFO MEMORY SAVER ===================================
graph_workflow = StateGraph(state_schema=MessagesState)
    
graph_workflow.add_node("chatbot",chatbot_node)
graph_workflow.add_edge(START,"chatbot")
# memory = SqliteSaver("langgraph.sqlite")

graph_workflow_compiled = graph_workflow.compile(checkpointer=memory)

def chat(message, thread_id= "sesion_terminal"):
    config = { "configurable": {"thread_id": thread_id }}
    result = graph_workflow_compiled.invoke({"messages": [HumanMessage(content= message)]},config)
    return result["messages"][-1].content


#**************************************************************GRAFO MEMORY SAVER*********************************



#==============================================================GRAFO MEMORY DESLIZANTE ===================================
class windowedState(MessagesState):
    pass

graph_workflow_memory_deslizante = StateGraph(state_schema=windowedState)
    
graph_workflow_memory_deslizante .add_node("chatbot",chatbot_deslizante_node)
graph_workflow_memory_deslizante .add_edge(START,"chatbot")



# memory = PosgrestSaver.from_conn_string(
#      "postgresql://user:password@localhost:5432/pre_icfes_db"
# )
# memory = SqliteSaver("langgraph.sqlite")

graph_workflow_memory_deslizante_compiled = graph_workflow_memory_deslizante .compile(checkpointer=memory)

def chat_memory_deslizante(message, thread_id= "sesion_terminal"):
    config = { "configurable": {"thread_id": thread_id }}
    result = graph_workflow_memory_deslizante_compiled.invoke({"messages": [HumanMessage(content= message)]},config)
    return result["messages"][-1].content


#**************************************************************GRAFO MEMORY DESLIZANTE*********************************


# ===============================GUARDAR MEMORIA CON CHROMA (DB VECTORIAL)================================================================================

graph_workflow_memory_vector = StateGraph(state_schema=MessagesState)

graph_workflow_memory_vector.add_node("chatbot_vectorial",chat_vectorial_node)
graph_workflow_memory_vector.add_edge(START,"chatbot_vectorial")

graph_workflow_memory_vector_compiled = graph_workflow_memory_vector.compile(checkpointer=memory)

def chat_memory_vectorial(message, thread_id= "sesion_terminal"):
    config = { "configurable": {"thread_id": thread_id }}
    result = graph_workflow_memory_vector_compiled.invoke({"messages": [HumanMessage(content= message)]},config)
    return result["messages"][-1].content

def show_memories():
    try:
      results= vectorStore.get(['documents'])
      documents  = results.get('documents', [])
      if documents['documents'] :
          print("Memorias guardadas:")
          for i,memory in enumerate(documents):
              print(f"{i+1}: {memory}")
      else:
          print("No hay memorias guardadas.")
          return []
    except Exception as e:
        print(f"Error al recuperar memorias: {e}")
        return []


# ********************************************************GUARDAR MEMORIA CON CHROMA (DB VECTORIAL)***********************************************************************