"""Reglas de negocio para preparar y calificar evaluaciones académicas."""

from collections import defaultdict

from django.db import transaction

from Principal.models import IntentoEvaluacion, RespuestaEvaluacion

LETRAS_OPCIONES = ("A", "B", "C", "D")


def normalizar_preguntas(preguntas, materia):
    """Valida la salida del generador y conserva las claves solo del lado servidor."""
    if not isinstance(preguntas, list) or not preguntas:
        raise ValueError("No se generaron preguntas para esta evaluación.")

    normalizadas = []
    for indice, original in enumerate(preguntas):
        if not isinstance(original, dict):
            continue

        opciones = original.get("opciones")
        if not isinstance(opciones, dict):
            opciones = {letra: original.get(letra) for letra in LETRAS_OPCIONES}

        opciones_limpias = {
            letra: str(opciones[letra]).strip()
            for letra in LETRAS_OPCIONES
            if opciones.get(letra) is not None and str(opciones[letra]).strip()
        }
        correcta = str(
            original.get("respuesta_correcta", original.get("correcta", ""))
        ).strip().upper()
        enunciado = str(original.get("pregunta", "")).strip()

        if not enunciado or correcta not in opciones_limpias:
            continue

        competencia = str(original.get("competencia") or materia).strip()[:100]
        normalizadas.append(
            {
                "id": indice,
                "tipo": str(original.get("tipo") or "texto"),
                "competencia": competencia or materia[:100],
                "contexto": str(original.get("contexto") or ""),
                "pregunta": enunciado,
                "opciones": opciones_limpias,
                "respuesta_correcta": correcta,
                "explicacion": str(
                    original.get("explicacion")
                    or original.get("explicacion_correcta")
                    or f"Revisa el concepto de {competencia or materia} y compara cada opción con el enunciado."
                ),
                "error_comun": str(original.get("error_comun") or ""),
            }
        )

    if len(normalizadas) != len(preguntas):
        raise ValueError(
            "El generador devolvió preguntas incompletas o sin una respuesta correcta válida. "
            "Intenta generar el cuestionario nuevamente."
        )
    return normalizadas


def preguntas_para_estudiante(preguntas):
    """Construye la representación pública, excluyendo claves y retroalimentación."""
    return [
        {
            "id": pregunta["id"],
            "tipo": pregunta["tipo"],
            "competencia": pregunta["competencia"],
            "contexto": pregunta["contexto"],
            "pregunta": pregunta["pregunta"],
            "opciones": pregunta["opciones"],
        }
        for pregunta in preguntas
    ]


def calificar_y_guardar_evaluacion(estudiante, materia, preguntas, datos_respuesta):
    """Califica con datos del servidor y guarda el intento y sus respuestas atómicamente."""
    detalles = []
    conteo_competencias = defaultdict(lambda: {"aciertos": 0, "total": 0})

    for pregunta in preguntas:
        respuesta = str(datos_respuesta.get(f"respuesta_{pregunta['id']}", "")).strip().upper()
        if respuesta not in pregunta["opciones"]:
            respuesta = ""

        es_correcta = respuesta == pregunta["respuesta_correcta"]
        competencia = pregunta["competencia"][:100]
        conteo_competencias[competencia]["total"] += 1
        conteo_competencias[competencia]["aciertos"] += int(es_correcta)
        detalles.append(
            {
                **pregunta,
                "respuesta_estudiante": respuesta,
                "es_correcta": es_correcta,
            }
        )

    aciertos = sum(detalle["es_correcta"] for detalle in detalles)
    with transaction.atomic():
        intento = IntentoEvaluacion.objects.create(
            estudiante=estudiante,
            materia=materia[:100],
            total_preguntas=len(detalles),
            aciertos=aciertos,
        )
        RespuestaEvaluacion.objects.bulk_create(
            [
                RespuestaEvaluacion(
                    intento=intento,
                    numero=detalle["id"],
                    competencia=detalle["competencia"][:100],
                    enunciado=detalle["contexto"],
                    pregunta=detalle["pregunta"],
                    opciones=detalle["opciones"],
                    respuesta_estudiante=detalle["respuesta_estudiante"],
                    respuesta_correcta=detalle["respuesta_correcta"],
                    explicacion=detalle["explicacion"],
                    es_correcta=detalle["es_correcta"],
                )
                for detalle in detalles
            ]
        )

    competencias = [
        {
            "nombre": nombre,
            "aciertos": dato["aciertos"],
            "total": dato["total"],
            "porcentaje": round(100 * dato["aciertos"] / dato["total"], 1),
        }
        for nombre, dato in sorted(conteo_competencias.items())
    ]
    resultado = {
        "aciertos": aciertos,
        "total": len(detalles),
        "porcentaje": round(100 * aciertos / len(detalles), 1) if detalles else 0,
        "intento_id": intento.pk,
    }
    return resultado, detalles, competencias
