"""Evidencias de intervención: mediciones descriptivas no causales."""
from django.db.models import Q

from Principal.models import RespuestaEvaluacion


def contar_evidencias(estudiante, materia, competencia, antes_de=None, despues_de=None):
    """Solo respuestas de la competencia y materia del estudiante especificado."""
    filtro = (
        Q(competencia__iexact=competencia)
        | Q(competencia__iexact=f"{materia} · {competencia}")
    )
    queryset = RespuestaEvaluacion.objects.filter(
        intento__estudiante=estudiante,
    ).filter(filtro).filter(
        Q(intento__materia=materia)
        | Q(intento__materia__startswith="Simulacro:")
        | Q(intento__materia="Práctica adaptativa")
    )
    if antes_de is not None:
        queryset = queryset.filter(intento__fecha__lt=antes_de)
    if despues_de is not None:
        queryset = queryset.filter(intento__fecha__gt=despues_de)
    respuestas = list(queryset.order_by("-intento__fecha", "-pk")[:100])
    return sum(int(r.es_correcta) for r in respuestas), len(respuestas)
