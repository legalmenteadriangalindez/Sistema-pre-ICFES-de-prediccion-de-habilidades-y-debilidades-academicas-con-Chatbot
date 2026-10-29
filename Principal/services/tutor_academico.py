"""Contexto académico autorizado para el tutor conversacional."""

from Principal.models import IntentoEvaluacion, RespuestaEvaluacion


def construir_contexto_academico(estudiante):
    """Resume únicamente los resultados del estudiante de la solicitud actual."""
    if estudiante is None:
        return "Aún no hay un perfil de estudiante asociado a esta cuenta."

    intentos = list(
        IntentoEvaluacion.objects.filter(estudiante=estudiante)
        .order_by("-fecha")[:5]
    )
    if not intentos:
        return "Aún no hay evaluaciones registradas."

    lineas = [
        f"{intento.materia}: {intento.aciertos} de {intento.total_preguntas} aciertos"
        for intento in intentos
    ]
    errores = (
        RespuestaEvaluacion.objects.filter(
            intento__in=intentos,
            intento__estudiante=estudiante,
            es_correcta=False,
        )
        .select_related("intento")
        .order_by("-intento__fecha")[:6]
    )
    lineas.extend(
        f"Reforzar {respuesta.competencia}: {respuesta.explicacion[:160]}"
        for respuesta in errores
    )
    return "\n".join(lineas)
