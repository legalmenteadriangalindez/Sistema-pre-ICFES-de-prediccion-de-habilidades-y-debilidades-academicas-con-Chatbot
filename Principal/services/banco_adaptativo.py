"""Selección adaptativa por evidencias históricas; no es un modelo predictivo."""
from collections import defaultdict

from Principal.models import PreguntaBanco, RespuestaEvaluacion
from Principal.services.seguimiento import _materia
from Principal.services.repasos_espaciados import repasos_pendientes

MAX_PREGUNTAS = 5


def prioridades_estudiante(estudiante):
    """Agrupa respuestas propias: prioriza competencias con >=2 y <60% de aciertos.

    Se limita a 300 respuestas recientes; los resultados son orientativos y
    nunca se confunden con puntajes oficiales ICFES ni probabilidades ML.
    """
    ultimas = RespuestaEvaluacion.objects.filter(
        intento__estudiante=estudiante,
    ).select_related("intento").order_by("-intento__fecha", "-pk")[:300]
    conteos = defaultdict(lambda: [0, 0])
    areas = defaultdict(lambda: [0, 0])
    for respuesta in ultimas:
        materia = _materia(respuesta)
        if materia not in dict(PreguntaBanco.MATERIAS):
            continue
        competencia = respuesta.competencia.split(" · ", 1)[-1].strip().casefold()
        clave = (materia, competencia)
        conteos[clave][0] += 1
        conteos[clave][1] += int(respuesta.es_correcta)
        areas[materia][0] += 1
        areas[materia][1] += int(respuesta.es_correcta)
    debiles = {
        clave for clave, (n, aciertos) in conteos.items()
        if n >= 2 and aciertos / n < 0.6
    }
    areas_debiles = {
        materia for materia, (n, aciertos) in areas.items()
        if n >= 3 and aciertos / n < 0.6
    }
    return debiles, areas_debiles


def seleccionar_adaptativas(estudiante, cantidad=MAX_PREGUNTAS):
    """Usa exclusivamente preguntas activas aprobadas y evita repeticiones cuando hay alternativas."""
    if not 1 <= cantidad <= MAX_PREGUNTAS:
        raise ValueError("Cantidad de preguntas inválida.")
    preguntas = list(PreguntaBanco.objects.filter(
        estado="APROBADA", activo=True,
    ).order_by("pk")[:500])
    if not preguntas:
        return [], []

    debiles, areas_debiles = prioridades_estudiante(estudiante)
    usados = set(RespuestaEvaluacion.objects.filter(
        intento__estudiante=estudiante, pregunta_banco__isnull=False,
    ).values_list("pregunta_banco_id", flat=True))

    pendientes = {repaso.pregunta_id for repaso in repasos_pendientes(estudiante)}

    def ordenar(pregunta):
        foco = (
            0 if (pregunta.materia, pregunta.competencia.casefold()) in debiles
            else 1 if pregunta.materia in areas_debiles
            else 2
        )
        dificultad = {"BASICA": 0, "MEDIA": 1, "ALTA": 2}[pregunta.dificultad]
        return (pregunta.pk not in pendientes, pregunta.pk in usados, foco, dificultad, pregunta.pk)

    preguntas.sort(key=ordenar)
    elegidas = []
    if not debiles and not areas_debiles and not pendientes:
        # Sin diagnóstico: empezar con variedad de materias para medir mejor.
        vistos = set()
        for pregunta in preguntas:
            if pregunta.materia not in vistos:
                elegidas.append(pregunta)
                vistos.add(pregunta.materia)
                if len(elegidas) == cantidad:
                    break
    elegidas_ids = {p.pk for p in elegidas}
    for pregunta in preguntas:
        if len(elegidas) >= cantidad:
            break
        if pregunta.pk not in elegidas_ids:
            elegidas.append(pregunta)
            elegidas_ids.add(pregunta.pk)

    focos = [
        {"materia": m, "competencia": c}
        for m, c in sorted(debiles)
        if any(p.materia == m and p.competencia.casefold() == c for p in elegidas)
    ]
    return elegidas, focos


def preguntas_para_sesion(preguntas):
    """Conservar la respuesta solo en la sesión BD y nunca en el HTML inicial."""
    return [
        {
            "id": indice,
            "id_banco": pregunta.pk,
            "materia": pregunta.materia,
            "competencia": f"{pregunta.materia} · {pregunta.competencia}"[:100],
            "tipo": "texto",
            "contexto": pregunta.contexto,
            "pregunta": pregunta.enunciado,
            "opciones": pregunta.opciones,
            "respuesta_correcta": pregunta.respuesta_correcta,
            "explicacion": pregunta.explicacion,
            "dificultad": pregunta.dificultad,
        }
        for indice, pregunta in enumerate(preguntas)
    ]
