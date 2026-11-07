"""Indicadores descriptivos de ítems con umbrales explícitos de suficiencia."""
from collections import defaultdict
from math import ceil

from Principal.models import PreguntaBanco, RespuestaEvaluacion

MIN_ITEM = 20
MIN_DISCRIMINACION = 20
MIN_CONSISTENCIA = 30


def analizar_pregunta(pregunta):
    """Última respuesta por estudiante; no confundir con validez psicométrica."""
    registros = RespuestaEvaluacion.objects.filter(
        pregunta_banco=pregunta,
    ).select_related("intento").order_by("-intento__fecha", "-pk")
    unicos = {}
    for r in registros:
        unicos.setdefault(r.intento.estudiante_id, r)
    n = len(unicos)
    aciertos = sum(int(r.es_correcta) for r in unicos.values())
    indice = round(aciertos / n, 3) if n else None
    validados = []
    for r in unicos.values():
        intento = r.intento
        if intento.total_preguntas >= 4:
            resto = (intento.aciertos - int(r.es_correcta)) / (
                intento.total_preguntas - 1
            )
            validados.append((resto, int(r.es_correcta)))
    discriminacion = None
    if len(validados) >= MIN_DISCRIMINACION:
        validados.sort(key=lambda item: item[0])
        grupo = max(1, int(len(validados) * 0.27))
        bajos = validados[:grupo]
        altos = validados[-grupo:]
        discriminacion = round(
            sum(x[1] for x in altos) / grupo
            - sum(x[1] for x in bajos) / grupo, 3
        )
    if n < MIN_ITEM:
        alerta = "Muestra insuficiente para juzgar la calidad."
    elif indice >= 0.9:
        alerta = "Muy fácil: revisar nivel y distractores."
    elif indice <= 0.2:
        alerta = "Muy difícil: revisar claridad, clave y contenidos."
    elif discriminacion is not None and discriminacion < 0.2:
        alerta = "Discriminación baja: revisar el ítem."
    else:
        alerta = "Sin alerta automática; revisión pedagógica vigente."
    return {
        "pregunta": pregunta,
        "n": n,
        "aciertos": aciertos,
        "dificultad": indice,  # proporción de aciertos, no dificultad declarada
        "discriminacion": discriminacion,
        "alerta": alerta,
    }


def _varianza(valores):
    media = sum(valores) / len(valores)
    return sum((v - media) ** 2 for v in valores) / len(valores)


def consistencia_por_formulario():
    """Alfa solo para >=30 estudiantes y >=3 ítems idénticos por formulario.

    No mezclar intentos con preguntas diferentes. Es exploratorio,
    no acredita fiabilidad clínica ni equivalencia con ICFES.
    """
    filas = RespuestaEvaluacion.objects.filter(
        pregunta_banco__isnull=False,
    ).values_list(
        "intento_id", "intento__estudiante_id",
        "pregunta_banco_id", "es_correcta",
    ).order_by("intento_id")
    intentos = defaultdict(lambda: {"estudiante": None, "respuestas": {}})
    for intento_id, estudiante_id, pregunta_id, correcta in filas:
        fila = intentos[intento_id]
        fila["estudiante"] = estudiante_id
        fila["respuestas"][pregunta_id] = int(correcta)
    grupos = defaultdict(dict)
    for intento_id, fila in intentos.items():
        claves = tuple(sorted(fila["respuestas"]))
        if len(claves) >= 3:
            # Una sola observación por estudiante, nunca multiplicar su peso.
            grupos[claves].setdefault(fila["estudiante"], (intento_id, fila["respuestas"]))
    resultados = []
    for claves, alumnos in grupos.items():
        n = len(alumnos)
        if n < MIN_CONSISTENCIA:
            continue
        matriz = [list(fila[1][p] for p in claves) for fila in alumnos.values()]
        totales = [sum(fila) for fila in matriz]
        var_total = _varianza(totales)
        if var_total <= 0:
            alfa = None
        else:
            variancias = sum(
                _varianza([fila[i] for fila in matriz]) for i in range(len(claves))
            )
            alfa = round(len(claves) / (len(claves) - 1) * (1 - variancias / var_total), 3)
        resultados.append({
            "items": len(claves), "estudiantes": n, "alfa": alfa,
        })
    return sorted(resultados, key=lambda row: -row["estudiantes"])[:15]


def resumen_calidad(materia=""):
    queryset = PreguntaBanco.objects.filter(estado="APROBADA").order_by("-pk")
    if materia:
        queryset = queryset.filter(materia=materia)
    return [analizar_pregunta(p) for p in queryset[:100]]
