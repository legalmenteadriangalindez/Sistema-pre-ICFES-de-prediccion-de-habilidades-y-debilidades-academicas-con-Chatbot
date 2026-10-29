"""Transcripción de audio, cargada solo cuando se usa esta función."""

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def _cargar_modelo():
    try:
        import whisper
    except ImportError as error:
        raise RuntimeError(
            "La transcripción requiere los paquetes opcionales: instala requirements-audio.txt."
        ) from error

    return whisper.load_model(os.environ.get("WHISPER_MODEL", "base"))


def get_texto_de_audio(ruta: str) -> str:
    """Transcribe un archivo de audio usando el modelo configurado."""
    try:
        resultado = _cargar_modelo().transcribe(ruta)
    except FileNotFoundError as error:
        raise RuntimeError(
            "Whisper necesita FFmpeg instalado y disponible en PATH para procesar audio."
        ) from error
    return resultado["text"].strip()
