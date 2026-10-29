#===================================================IMPORTACIONES=============================================

from langgraph.graph import StateGraph
from .state import StudentState,generatorQuestions
from langgraph.graph import START,END

from .nodes import (generar_pregunta,generar_material,registry_history)

#****************************************************IMORTACIONES********************************************************





#==============================================================GRAFO GENERAR PREGUNTAS===================================
graph_generate = StateGraph(generatorQuestions)

graph_generate.add_node("generar",generar_pregunta )


graph_generate.add_edge(START,"generar")
graph_generate.add_edge("generar",END)


graph_gen_compile=graph_generate.compile() # analizar si es viable usar un checkpoint ara guardar el estado del grafo 

def init_graph_generator(competencia: str)->generatorQuestions:
    initial_state: generatorQuestions = {
        "competencia": competencia,
        "preguntas": []
        
    }
    return initial_state
#**************************************************************GRAFO GENERAR PREGUNTAS *********************************






#========================================GRAFO EVALUACION==================================================
graph_evaluation = StateGraph(StudentState)


graph_evaluation.add_node("generar_material",generar_material)
graph_evaluation.add_node("registrar_historial",registry_history)



graph_evaluation.add_edge(START,"generar_material")
graph_evaluation.add_edge("generar_material","registrar_historial")
graph_evaluation.add_edge("registrar_historial",END)


graph_evaluation_compiled= graph_evaluation.compile() # analizar si es viable usar un checkpoint ara guardar el estado del grafo 


def init_graph_evaluation(preguntas: list[str])->StudentState:
    initial_state: StudentState = {
        "preguntas": preguntas,
        "historial": [],
        "tematicas_recomendadas": [],
    }
    return initial_state

#**************************************************************GRAFO EVALUACION******************************************


