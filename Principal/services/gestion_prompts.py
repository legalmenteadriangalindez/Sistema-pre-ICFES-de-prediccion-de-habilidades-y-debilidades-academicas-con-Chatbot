"""Servicio activo de generación de preguntas y temas de estudio."""
from Principal.IA.chains import chain_cuestionarios, chain_maateriales

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
