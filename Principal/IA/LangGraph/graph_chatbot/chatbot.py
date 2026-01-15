# =====================================================IMPORTS ================================================================
from langgraph.graph import StateGraph, START, END

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from Principal.IA.llm import chat_bot

from Principal.IA.chains import get_response_generation_chain

from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder

from langchain_core.messages import HumanMessage,trim_messages,AIMessage,BaseMessage

from .memory_manager import ModernMemoryManager

from Principal.IA.LangGraph.graph_chatbot.states import MemoryState

import os 

# ****************************************************IMPORTS***************************************************************************


class ModernChatbot:
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_manager = ModernMemoryManager(user_id)

        # configuracion del modelo llm 

        self.llm = chat_bot  #.get_num_tokens
        
        self.system_template = """Eres un asistente personal inteligente y amigable.
                               Características de tu personalidad:
                               - Eres útil, empático y conversacional
                               - Recuerdas información importante de conversaciones anteriores
                               - Adaptas tu estilo a las preferencias del usuario
                               - Eres proactivo ofreciendo sugerencias relevantes
                               - Mantienes un tono profesional pero cercano
                               
                               {context}
                               
                               Usa esta información para personalizar tus respuestas, pero no menciones explícitamente que tienes memoria a menos que sea relevante para la conversación."""
        
        # configurar el treaming de mensajes
        self.messages_trimmer = trim_messages(
            strategy= "last",
            max_tokens= 2000,
            token_counter= self.llm,
            start_on = "human",
            include_system= True
        )

        # crear la aplicacion de langraph 
        self.app_graph = self._create_app_graph()
        
    def _create_app_graph(self):
        workflow = StateGraph(state_schema=MemoryState)

        # 
        def memory_retrieval_node(state):
            messages = state['messages']

            if not messages:
                return {"vector_memories": []}
            
            # obtener el ultimo mensage del usuario
            last_user_message = None
            

            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break
            if not last_user_message:
                return {"vector_memories": []}
            
            # buscar memorias vectoriales relevantes 
            relevant_memories = self.memory_manager.search_vector_memory(last_user_message.content)
            return {"vector_memories": relevant_memories}
        
        def context_optimization_node(state: MemoryState):
            messages = state['messages']
            trimmed_messages = self.messages_trimmer.invoke(messages)  
            
            return {"messages": trimmed_messages}
        
        # nodo que genera la respuesta usando el contexto optimizado y las memorias vectoriales
        def response_generation_node(state):
            messages = state['messages']
            vector_memories = state.get('vector_memories', [])
    
            if not messages:
                return {"messages": []}
            
            # construir el contexto a partir de las memorias vectoriales
            if vector_memories:
                context_parts = ["Informacion relevante que recuerdas del usuario:"]
                for memory in vector_memories:
                    context_parts.append(f"- {memory}")
                context = "\n".join(context_parts)
            else:
                context = "No hay contexto previo disponible."

            # Crear el prompt con el contexto dinamico
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_template.format(context=context)),
                MessagesPlaceholder(variable_name="messages")
            ])

            # Generar la respuesta
            chain = prompt | self.llm
            response = chain.invoke({"messages": messages})
            if not isinstance(response, AIMessage):
                response = AIMessage(content=str(response))
            return {"messages": response}
        
        # nodo que extrae y almacena nuevas memorias vectoriales
        def memory_extraction_node(state):
            messages = state['messages']
    
            last_extraction = state.get('last_memory_extraction')
    
            # obtener el ultimo mensage del usuario
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break
            
            if not last_user_message:
                return {}
            # procesar solo si no hemos extraido memoria recientemente de este mensage
            if last_extraction != last_user_message.content:
                extracted_memories =self.memory_manager.extract_and_store_memories(last_user_message.content)
                if not extracted_memories or not isinstance(extracted_memories, list):
                    extracted_memories = []
                valid_memories = [
                mem for mem in extracted_memories
                if getattr(mem, "content", "").strip() and getattr(mem, "importance", 0) >= 2
                ]
                # Guardar solo las memorias válidas
                for mem in valid_memories:
                    self.memory_manager.save_memory_vectorial(mem)

                return {"last_memory_extraction": last_user_message.content}
            return {}
        
        # configuarar el grafo con flujo secuencial de nodos
        workflow.add_node("memory_retrieval", memory_retrieval_node)
        workflow.add_node("context_optimization", context_optimization_node)
        workflow.add_node("response_generation", response_generation_node)
        workflow.add_node("memory_extraction", memory_extraction_node)
    
        # definir el flujo del grafo
        workflow.add_edge(START, "memory_retrieval")
        workflow.add_edge("memory_retrieval", "context_optimization")
        workflow.add_edge("context_optimization", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", END)
        
        # return workflow
    
    
   # configurar el guardado de checkpoints en sqlite
        db_path = os.path.join(
           self.memory_manager.user_dir,
             "langgraph_memory.db"
           
        )    
    
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)       
        return workflow.compile(checkpointer=checkpointer)

    # enviar u n mensaje al chatbot y obtener la respuesta del chatbot
    def chat(self, user_message: str, chat_id: str = "default"):
        try : 
            config = {"configurable": {"thread_id": f"user_chat_{self.user_id}_{chat_id}"}}

            # actualizar el titulo del chat esi es nesesario
            chat_info = self.memory_manager.get_chat_info(chat_id)

            # si es la primera vez que se ejecuta el chat no existe 
            if chat_info is None:
                chat_id = self.memory_manager.create_new_chat(user_message) 
                chat_info = self.memory_manager.get_chat_info(chat_id)

            if chat_info['title'] == "Nuevo Chat":
                chat_title =self.memory_manager.generate_chat_title(user_message)
                self.memory_manager.update_chat_metadata(chat_id,chat_title)
            
            # invocar el chatbot con el nuevo mensaje del usuario
            result = self.app_graph.invoke(
                {"messages": [HumanMessage(content=user_message)]},
                config
            )
             
            assistant_response = result['messages'][-1].content
            print(assistant_response)
            return{
                "success": True,
                "response": assistant_response,
                "error": None,
                "memory_used": len(result.get('vector_memories', [])),
                "context_optimized": True
            }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e),
                "memory_used": 0,
                "context_optimized": False
            }
        
    # obtiener el historial de conversaciones para un chat especifico
    def get_conversation_history(self, chat_id: str = "default",limit : int = 50):
        try: 
            config = {"configurable":{"thread_id": f"user_chat_{self.user_id}_{chat_id}"}}

            state = self.app_graph.get_state(config)

            if not state.values or "messages" not in state.values:
               return []
             
            messages = state.values["messages"]
            
            history = []
            for msg in messages[-limit:]:
                if isinstance(msg, (HumanMessage, AIMessage)):
                     history.append({"role": "user" if isinstance(msg, HumanMessage) else "assistant",
                                     "content": msg.content,
                                     "timestamp": getattr(msg, "timestamp", None) or "2026-01-01T00:00:00"
                                     })
            return history
        except Exception as e:
            print("Error retrieving conversation history:", e)
            return []
    
    # limpiar el historial de conversaciones para un chat especifico
    def clear_conversation(self, chat_id: str = "default") -> bool:
        try:
            config = {"configurable": {"thread_id": f"user_chat_{self.user_id}_{chat_id}"}}
            
            # Crear un estado vacío para "resetear" la conversación
            self.app_graph.invoke({"messages": []}, config)
            return True
        
        except Exception as e:
            print(f"Error clean conversation: {e}")
            return False
    
    # eliminar un chat específico de langgraph
    def delete_chat_from_langgraph(self, chat_id: str) -> bool:
    
        try:
            thread_id = f"user_chat_{self.user_id}_{chat_id}" 
            # Crear un estado vacío para "limpiar" el thread
            config = {"configurable": {"thread_id": thread_id}}
            
            # Obtener al estado actual para vantificar el existe
            try: 
                current_state = self.app_graph.get_state(config)
                if not current_state.values:
                    return True  # Ya no existe
            except:
                return True  # No existe o error accediendo
            
            # No hay una API pública para eliminar threads en LangGraph
            # Por ahora, simplemente reportamos éxito
            # La eliminación real sería manejada por la base de datos con una consulta directa por ejemplo (SQL DELETE)
            return True
        
        except Exception as e:
            print(f"Error eliminando chat de LangGraph: {e}")
            return False


class chatbotManager:

    _instances= {}

    @classmethod
    def get_chatbot(cls,user_id):
        if user_id not in cls._instances:
            cls._instances[user_id] = ModernChatbot(user_id)
        return cls._instances[user_id]

    @classmethod
    def remove_chatbot(cls,user_id):
        if user_id in cls._instances:
            del cls._instances[user_id]
    
    @classmethod
    def clear_all_chatbots(cls):
        cls._instances.clear()