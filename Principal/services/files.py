#======================================IMPORTACIONES=============================================
import os # se utiliza para crear rutas ara la entrada de audio 
from django.core.files.storage import FileSystemStorage

#***************************************IMPORTACIONES********************************************




#======================================GUARDAR PDFs=============================================
def guardar_PDFs(pdf):
    fs = FileSystemStorage(location="media/pdfs")
    nombre = fs.save(pdf.name, pdf)
    return fs.path(nombre)

#**************************************GUARDAR PDFs**********************************************




#======================================GUARDAR AUDIOS=============================================
def guardar_audio(audio):
    archivos_dir ='media/audios'
    os.makedirs(archivos_dir,exist_ok=True)
    ruta = os.path.join(archivos_dir,audio.name)

    with open(ruta,'wb+') as destino:
     for chunk in audio.chunks():
        destino.write(chunk)
    
    return ruta
#************************************GUARDAR AUDIOS**********************************************

