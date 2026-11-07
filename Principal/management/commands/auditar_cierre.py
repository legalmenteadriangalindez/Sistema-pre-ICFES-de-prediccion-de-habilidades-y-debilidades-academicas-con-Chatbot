"""Auditoría de cierre no destructiva sobre la base de datos del servidor.

Uso:
    python manage.py auditar_cierre
    python manage.py auditar_cierre --ollama

No crea cuentas, no entrena, no publica modelos y no muestra datos personales.
La comprobación de Ollama es opcional y usa una pregunta sintética.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand

from Principal.models import Estudiante, IntentoEvaluacion, RespuestaEvaluacion
from Principal.services.prediccion_academica import auditar_datos, cargar_modelo


def comprobar_ollama():
    """Comprueba generación REAL, sin información académica o personal."""
    from Principal.IA.llm import OLLAMA_BASE_URL, OLLAMA_MODEL

    if not OLLAMA_BASE_URL.startswith(("http://127.0.0.1:", "http://localhost:", "http://[::1]:")):
        return {
            "estado": "omitido",
            "motivo": "Por seguridad solo se comprueba Ollama en localhost.",
        }

    cuerpo = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": "Responde en español con una frase breve: ¿cuánto es dos más dos?",
        "stream": False,
        "options": {"num_predict": 40},
    }).encode("utf-8")
    solicitud = Request(
        OLLAMA_BASE_URL + "/api/generate",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(solicitud, timeout=45) as respuesta:
            datos = json.loads(respuesta.read(512 * 1024))
        texto = str(datos.get("response") or "").strip()
        return {
            "estado": "correcto" if texto else "sin_respuesta",
            "modelo": OLLAMA_MODEL,
            "respuesta_recibida": bool(texto),
        }
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {"estado": "no_disponible", "tipo_error": type(exc).__name__}


class Command(BaseCommand):
    help = "Diagnóstico real, de solo lectura, de evaluaciones, predicción y Ollama opcional."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ollama", action="store_true",
            help="Probar una respuesta real de Ollama local con una pregunta ficticia.",
        )

    def handle(self, *args, **options):
        auditoria = auditar_datos()
        modelo = cargar_modelo()
        resultado = {
            "operacion": "solo_lectura",
            "estudiantes_registrados": Estudiante.objects.count(),
            "evaluaciones_registradas": IntentoEvaluacion.objects.count(),
            "respuestas_registradas": RespuestaEvaluacion.objects.count(),
            "prediccion": {
                "estudiantes_elegibles": auditoria.get("estudiantes", 0),
                "ejemplos": auditoria.get("ejemplos", 0),
                "casos_riesgo": auditoria.get("casos_riesgo", 0),
                "casos_sin_riesgo": auditoria.get("casos_sin_riesgo", 0),
                "suficiente_para_intentar": auditoria["suficiente_para_intentar"],
                "modelo_validado_disponible": modelo is not None,
            },
            "ollama": comprobar_ollama() if options["ollama"] else {
                "estado": "no_comprobado",
                "motivo": "Ejecuta --ollama para generar una respuesta real.",
            },
            "limitaciones": [
                "La base local nunca se sube a GitHub.",
                "La prediccion solo es valida con datos suficientes y modelo aprobado.",
                "Esta prueba de Ollama no verifica por si sola LangGraph, ChromaDB ni adjuntos.",
            ],
        }
        self.stdout.write(json.dumps(resultado, ensure_ascii=False, indent=2))
