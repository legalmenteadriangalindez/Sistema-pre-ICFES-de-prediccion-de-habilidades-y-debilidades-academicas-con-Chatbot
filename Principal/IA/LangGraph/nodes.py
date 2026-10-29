# ====================================================IMPORTACIONES ===========================================================

from .state import StudentState,generatorQuestions

from Principal.services.gestion_prompts import get_respuesta,get_material_recomendado

from copy import deepcopy 

# ****************************************************IMPORTACIONES ***************************************************************************



# =========================================NODO PARA GENERAR CUESTIONARIOS ======================================================================

def generar_pregunta(state: generatorQuestions, competencia: str= None)->generatorQuestions:
    competencia_final = competencia or state.get("competencia","")
    preguntas = state.get("preguntas",[])
    pregunta = get_respuesta(competencia_final)
    p = deepcopy(pregunta)
    p["id"] = len(preguntas)
    print("---------------genero preguntas--------")
    return {
        **state,
        "preguntas": preguntas + [p]
    }

# *************************************************************************************************************************************************



# =========================================NODO PARA GENERAR MATERIAL RECOMENDADO =======================================================================================================

def generar_material(state: StudentState)->StudentState:
    
    new_state = dict(state)
    
    preguntas= new_state.get("preguntas",[])
    tematicas_recomendadas = []
    for pregunta in preguntas: 
        resultado = get_material_recomendado(
            contexto = pregunta.get("contexto",""),
        )
        tematicas_recomendadas.append({
            "tematicas_recomendadas": resultado.get("tematicas_recomendadas",[])
        })
    new_state["tematicas_recomendadas"] = tematicas_recomendadas
    print("----------genero material por pregunta--------")
    return new_state

# *******************************************NODO PARA GENERAR MATERIAL RECOMENDADO *****************************************************************************************************************




# =============================================NODO PARA GUARDAR EL HISTORIAL ===================================================================================================
def registry_history(state: StudentState)->StudentState:
    historial = state.get("historial",[])

    registro = {
        
        "tematicas_recomendadas": state.get("tematicas_recomendadas",[]),

    }
    new_state = dict(state)
    new_state["historial"]= historial + [registro]
    print("--------------guardo historial-------------")
    return new_state

# *******************************************************************************************************************************************************************