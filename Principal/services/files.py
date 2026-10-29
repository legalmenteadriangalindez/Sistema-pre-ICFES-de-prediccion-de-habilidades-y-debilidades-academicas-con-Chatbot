from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def guardar_PDFs(pdf):
    storage = FileSystemStorage(location=settings.MEDIA_ROOT / "pdfs")
    nombre = storage.save(Path(pdf.name).name, pdf)
    return storage.path(nombre)


def guardar_audio(audio):
    directorio = settings.MEDIA_ROOT / "audios"
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / Path(audio.name).name

    with ruta.open("wb+") as destino:
        for fragmento in audio.chunks():
            destino.write(fragmento)

    return str(ruta)
