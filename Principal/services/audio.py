#======================================IMPORTACIONES=============================================

from Principal.IA.processorAudio import get_texto_de_audio # importacion de la funcion para extraer texto de los audios 

from .files import guardar_audio
#*******************************************IMPORTACIONES****************************************


#======================================PROCESAR AUDIOS=============================================
def procesar_audio(audio):
    if not audio:
        return None,None
    ruta = guardar_audio(audio)
    texto = get_texto_de_audio(ruta)
    return texto,ruta
#**************************************PROCESAR AUDIOS**********************************************

