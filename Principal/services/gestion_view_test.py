# ====================================================IMPORTACIONES ===========================================================


from Principal.IA.LangGraph.graph import init_graph_evaluation,init_graph_generator, graph_gen_compile,graph_evaluation_compiled


#*****************************************IMORTACIONES****************************************



# ===========================================FUNCION PARA GENERAR N CANDIDAD DE QUIZ===========================================================
def generar_quizes(materia: str, cantidad: int)->list[dict]:
    state= init_graph_generator(materia)
    for _ in range(cantidad):
        state = graph_gen_compile.invoke(state)
    
    return state["preguntas"]
#*****************************************FUNCION PARA GENERAR N CANDIDAD DE QUIZ****************************************



# ===========================================FUNCION PARA GENERAR MATERIAL RECOMENDADO===========================================================

def generar_material(preguntas: list[dict])->list[dict]:
    state = init_graph_evaluation(preguntas)
    state = graph_evaluation_compiled.invoke(state)
    
    return [
       tema 
       for bloque in state.get("tematicas_recomendadas",[])
       for tema in bloque.get("tematicas_recomendadas",[])      
    ]
#*****************************************FUNCION PARA GENERAR MATERIAL RECOMENDADO****************************************

#======================================FUNCION PARA GESTIONAR TURNO DE LOS MENSAGES================================================
def agrupar_historial_por_turnos(historial):
    turnos = []
    turno_actual = {}
    for msg in historial:
        if msg["role"] == "user":
            turno_actual = {"usuario": msg["content"], "respuesta": None}
        elif msg["role"] == "assistant" and turno_actual:
            turno_actual["respuesta"] = msg["content"]
            turnos.append(turno_actual)
            turno_actual = {}
    return turnos
#**************************************FUNCION PARA GESTIONAR TURNO DE LOS MENSAGES**************************************************





