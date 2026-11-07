"""Cuestionarios originales sin Ollama para demostraciones en Render Free."""
from Principal.services.simulacros_banco import BANCO


def generar_quiz_demo(materia):
    """Usa preguntas revisables del banco local sin llamar servicios externos."""
    preguntas = BANCO.get(materia, ())
    if not preguntas:
        raise ValueError("No hay preguntas de demostración para esta materia.")

    return [
        {
            "pregunta": pregunta,
            "opciones": dict(opciones),
            "respuesta_correcta": clave,
            "competencia": competencia,
            "explicacion": explicacion,
            "contexto": "",
        }
        for pregunta, opciones, clave, competencia, explicacion in preguntas
    ]
