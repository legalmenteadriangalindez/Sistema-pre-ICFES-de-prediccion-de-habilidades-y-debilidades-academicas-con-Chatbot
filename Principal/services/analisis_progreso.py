"""Comparación descriptiva pre/post por competencia y área del mismo alumno."""
from collections import defaultdict

from Principal.models import RespuestaEvaluacion
from Principal.services.seguimiento import _materia

MIN_POR_CORTE = 3


def comparar_progreso(estudiante):
    """Comparar las primeras y últimas 3 evidencias de cada competencia.

    Siempre mostramos falta de evidencia; no atribuimos causalidad a la IA.
    """
    registros = RespuestaEvaluacion.objects.filter(
        intento__estudiante=estudiante,
    ).select_related("intento").order_by("intento__fecha", "pk")[:1000]
    grupos = defaultdict(list)
    for respuesta in registros:
        materia = _materia(respuesta)
        if not materia:
            continue
        competencia = respuesta.competencia.split(" · ", 1)[-1].strip()
        grupos[(materia, competencia)].append(int(respuesta.es_correcta))
    filas = []
    for (materia, competencia), datos in sorted(grupos.items()):
        cantidad = len(datos)
        if cantidad >= 2 * MIN_POR_CORTE:
            n = MIN_POR_CORTE
            antes = round(sum(datos[:n]) * 100 / n, 1)
            despues = round(sum(datos[-n:]) * 100 / n, 1)
            cambio = round(despues - antes, 1)
        else:
            antes = despues = cambio = None
        filas.append({
            "materia": materia, "competencia": competencia,
            "respuestas": cantidad, "antes": antes,
            "despues": despues, "cambio": cambio,
        })
    return sorted(filas, key=lambda x: (x["cambio"] is None, x["materia"], x["competencia"]))
