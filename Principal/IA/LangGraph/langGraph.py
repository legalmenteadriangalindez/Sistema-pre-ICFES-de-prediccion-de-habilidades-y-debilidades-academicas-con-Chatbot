from typing import TypedDict,Annotated,Optional

from langgraph.graph import StateGraph,START,END

from operator import add
#=====================================PASOS PARA DEFINIR UN LANGGRAPH=========================================================

# DEFINIR EL ESTADO DEL ESQUEMA
class state(TypedDict):
    texto_original: str
    texto_mayuscula: str
    longitud: int
    resultado: str
#    respuesta: Opcional[str]  # opcinal
    logs: Annotated[list[str],add]


# 2 CREAR EL GARFO DE ESTADO 
graph = StateGraph(state)

# 3 DEFNIR LAS FUNCINES DE LOS NODOS 
def poner_mayusculas(state):
    texto = state["texto_original"]
    return {
        "texto_mayuscula": texto.upper(),
        "logs": "paso 1 completed"
        }

def contar_caracteres(state):
    texto= state["text_mayus"]
    return {"longitud": len(texto),
            "logs": "paso 2 completed"
            }
def es_par(state):
    return{"resultado": "es par"}

def es_impar(state):
    return{"resultado": "es impar"}

# funcion decide_branch "decidir rama"

def decide_branch(state):
    if state["longitud"] % 2 == 0:
        return "par"
    else :
        return "impar"

# 4 AÑADIR LOS NODOS AL GRAFO
graph.add_node("mayusculas", poner_mayusculas)
graph.add_node("contar",contar_caracteres)
graph.add_node("par",es_par)
graph.add_node("impar",es_impar)


# 5 CONECTAR LOS NODOS EN SECUENCIA USANDO LAS ARISTAS 
graph.add_edge(START,"mayusculas")
graph.add_edge("mayusculas","contar")
graph.add_conditional_edges("contar",decide_branch)
graph.add_node("par",END)
graph.add_edge("impar",END)

# 6 COMPILAR EL GRAFO
graph_compiled= graph.compile()


# 7 INVOCAR EL GRAFO (EN OCACIONES TENDRA ESTADO INICIAL Y EN OTRAS NO )
initial_state = {"texto_original": "hola mundo"}
result = graph_compiled.invoke(initial_state)
print(result)




#*************************************PASOS PARA DEFINIR UN LANGGRAPH*********************************************************

