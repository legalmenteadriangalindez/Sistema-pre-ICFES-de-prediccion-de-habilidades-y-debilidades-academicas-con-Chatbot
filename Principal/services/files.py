"""Almacenamiento privado y validado de documentos del tutor.

No servir estas carpetas mediante MEDIA_URL ni STATIC_URL.
La extensión y el MIME declarados por el navegador nunca son suficientes:
también se valida la cabecera real del archivo.
"""
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage

PDF_MAX_BYTES = 10 * 1024 * 1024
AUDIO_MAX_BYTES = 25 * 1024 * 1024
AUDIO_FORMATOS = {".wav", ".mp3", ".ogg", ".opus", ".m4a", ".webm"}


def _extension(archivo):
    return Path(getattr(archivo, "name", "") or "").suffix.lower()


def _cabecera(archivo, longitud=32):
    posicion = archivo.tell() if hasattr(archivo, "tell") else 0
    try:
        archivo.seek(0)
        return archivo.read(longitud)
    finally:
        archivo.seek(posicion)


def _validar_tamano(archivo, limite):
    tamanio = getattr(archivo, "size", None)
    if tamanio is None or not 0 < tamanio <= limite:
        raise ValidationError(
            f"El archivo debe tener contenido y no superar {limite // (1024 * 1024)} MB."
        )


def validar_pdf(archivo):
    if _extension(archivo) != ".pdf":
        raise ValidationError("Solo se admiten documentos PDF.")
    _validar_tamano(archivo, PDF_MAX_BYTES)
    if not _cabecera(archivo).startswith(b"%PDF-"):
        raise ValidationError("El archivo no contiene una cabecera PDF válida.")


def validar_audio(archivo):
    extension = _extension(archivo)
    if extension not in AUDIO_FORMATOS:
        raise ValidationError("Formato de audio no admitido. Usa WAV, MP3, OGG, OPUS, M4A o WEBM.")
    _validar_tamano(archivo, AUDIO_MAX_BYTES)
    inicio = _cabecera(archivo)
    valido = {
        ".wav": inicio.startswith(b"RIFF") and inicio[8:12] == b"WAVE",
        ".mp3": inicio.startswith(b"ID3") or (
            len(inicio) > 1 and inicio[0] == 0xFF and (inicio[1] & 0xE0) == 0xE0
        ),
        ".ogg": inicio.startswith(b"OggS"),
        ".opus": inicio.startswith(b"OggS"),
        ".m4a": inicio[4:8] == b"ftyp",
        ".webm": inicio.startswith(bytes.fromhex("1a45dfa3")),
    }[extension]
    if not valido:
        raise ValidationError("La cabecera del audio no corresponde al formato seleccionado.")


def _guardar_privado(archivo, user_id, subcarpeta):
    try:
        identificador = int(user_id)
    except (ValueError, TypeError):
        raise ValidationError("Debes iniciar sesión para adjuntar archivos.")
    if identificador <= 0:
        raise ValidationError("Identificador de usuario inválido.")

    raiz = Path(settings.PRIVATE_UPLOAD_ROOT)
    carpeta = raiz / str(identificador) / subcarpeta
    carpeta.mkdir(mode=0o700, parents=True, exist_ok=True)
    almacenamiento = FileSystemStorage(
        location=str(carpeta),
        base_url=None,
        file_permissions_mode=0o600,
        directory_permissions_mode=0o700,
    )
    # No reutilizar nombres del cliente: evita sobrescrituras y path traversal.
    archivo.seek(0)
    nombre = almacenamiento.save(uuid4().hex + _extension(archivo), archivo)
    return almacenamiento.path(nombre)


def guardar_PDFs(pdf, user_id=None):
    validar_pdf(pdf)
    return _guardar_privado(pdf, user_id, "pdfs")


def guardar_audio(audio, user_id=None):
    validar_audio(audio)
    return _guardar_privado(audio, user_id, "audios")
