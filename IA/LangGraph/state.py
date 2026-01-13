# ====================================================IMPORTACIONES ===========================================================

from typing import TypedDict,Annotated

from operator import add

#****************************************************IMORTACIONES********************************************************



#==================================================STATE GENERAR PREGUNTAS =======================================
class generatorQuestions(TypedDict):
    competencia : str
    preguntas : list[dict]

#************************************************STATE GENERAR PREGUNTAS************************************************



# ==============================================STATE EVALUACION =====================================

class StudentState(TypedDict):

    preguntas: list[dict]

    tematicas_recomendadas: list[dict]

    historial: Annotated[list[dict], add]

#************************************************STATE EVALUACION************************************************



