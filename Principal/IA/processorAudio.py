# =====================================IMPPORTACIONES=========================================
import os

os.environ["PATH"] += r";C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin"

import whisper 

import tempfile

import os

# ************************************ IMPORTACIONES *******************************************



# ==================================================FUNCION PARA EXTRAER TEXTO DE AUDIO===========================================================================================================================
model = whisper.load_model("base")

def get_texto_de_audio(ruta:str):
 resultado = model.transcribe(ruta)
#  os.remove(ruta)
 return resultado["text"]

#**************************************FUNCION PARA EXTRAER TEXTOS PDFs***********************************************************************************************


