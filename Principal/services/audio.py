#======================================IMPORTACIONES=============================================

from Principal.IA.processorAudio import get_texto_de_audio # importacion de la funcion para extraer texto de los audios 

from .files import guardar_audio
#*******************************************IMPORTACIONES****************************************


#======================================PROCESAR AUDIOS=============================================
def procesar_audio(audio, user_id=None):
    if not audio:
        return None,None
    ruta = guardar_audio(audio, user_id=user_id)
    texto = get_texto_de_audio(ruta)
    return texto,ruta
#**************************************PROCESAR AUDIOS**********************************************

