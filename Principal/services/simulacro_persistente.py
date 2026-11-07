"""Estado y guardado atómico del simulacro de 50 preguntas y dos bloques.

No pretende reproducir el volumen, puntaje IRT ni tiempos oficiales ICFES.
"""
from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from Principal.models import (
    Estudiante, IntentoEvaluacion, RespuestaEvaluacion, SimulacroAvanzado,
)
from Principal.simulacros_views import crear_preguntas

PREGUNTAS_POR_BLOQUE = 25
SEGUNDOS_BLOQUE = 75 * 60


def obtener_activo(estudiante, bloquear=False):
    consulta = SimulacroAvanzado.objects.filter(
        estudiante=estudiante, estado__in=("EN_CURSO", "PAUSADO"),
    )
    if bloquear:
        consulta = consulta.select_for_update()
    return consulta.order_by("-pk").first()


def segundos_disponibles(examen):
    if examen.estado == "EN_CURSO":
        return max(0, int((examen.vence_en - timezone.now()).total_seconds()))
    return examen.restantes_segundos


def sincronizar(examen):
    """Caducidad se verifica en servidor, no se confía en el temporizador JS."""
    if examen.estado == "EN_CURSO" and timezone.now() >= examen.vence_en:
        examen.restantes_segundos = 0
        examen.estado = "PAUSADO"
        examen.save(update_fields=("restantes_segundos", "estado", "actualizado_en"))


@transaction.atomic
def iniciar(estudiante):
    Estudiante.objects.select_for_update().get(pk=estudiante.pk)
    existente = obtener_activo(estudiante, bloquear=True)
    if existente is not None:
        sincronizar(existente)
        return existente
    preguntas = crear_preguntas("Integral ampliado")
    if len(preguntas) != PREGUNTAS_POR_BLOQUE * 2:
        raise ValueError("El banco de práctica debe contener 50 preguntas.")
    ahora = timezone.now()
    return SimulacroAvanzado.objects.create(
        estudiante=estudiante, preguntas=preguntas,
        vence_en=ahora + timedelta(seconds=SEGUNDOS_BLOQUE),
        restantes_segundos=SEGUNDOS_BLOQUE,
    )


@transaction.atomic
def actualizar(estudiante, accion, indice=None, valor=None):
    examen = obtener_activo(estudiante, bloquear=True)
    if examen is None:
        raise ValueError("No existe un simulacro activo.")
    sincronizar(examen)

    if accion == "guardar":
        if examen.estado != "EN_CURSO":
            raise ValueError("Reanuda el simulacro antes de guardar respuestas.")
        if indice is None or not isinstance(indice, int):
            raise ValueError("Número de pregunta inválido.")
        inicio = (examen.bloque - 1) * PREGUNTAS_POR_BLOQUE
        if not inicio <= indice < inicio + PREGUNTAS_POR_BLOQUE:
            raise ValueError("Esta pregunta pertenece a otro bloque.")
        pregunta = examen.preguntas[indice]
        if valor not in pregunta["opciones"] and valor != "":
            raise ValueError("La alternativa enviada no es válida.")
        respuestas = dict(examen.respuestas)
        if valor:
            respuestas[str(indice)] = valor
        else:
            respuestas.pop(str(indice), None)
        examen.respuestas = respuestas
        examen.save(update_fields=("respuestas", "actualizado_en"))
        return examen

    if accion == "pausar":
        if examen.estado == "EN_CURSO":
            examen.restantes_segundos = segundos_disponibles(examen)
            examen.estado = "PAUSADO"
            examen.save(update_fields=("restantes_segundos", "estado", "actualizado_en"))
        return examen

    if accion == "reanudar":
        if examen.estado != "PAUSADO" or examen.restantes_segundos <= 0:
            raise ValueError("Este bloque agotó el tiempo disponible.")
        examen.vence_en = timezone.now() + timedelta(seconds=examen.restantes_segundos)
        examen.estado = "EN_CURSO"
        examen.save(update_fields=("vence_en", "estado", "actualizado_en"))
        return examen

    if accion == "siguiente_bloque":
        if examen.bloque != 1:
            raise ValueError("Ya se encuentra en el segundo bloque.")
        examen.bloque = 2
        examen.estado = "PAUSADO"
        examen.restantes_segundos = SEGUNDOS_BLOQUE
        examen.save(update_fields=(
            "bloque", "estado", "restantes_segundos", "actualizado_en",
        ))
        return examen

    if accion == "finalizar":
        if examen.bloque != 2:
            raise ValueError("Debes cerrar primero el bloque uno.")
        return calificar(examen)

    raise ValueError("Acción no reconocida.")


def calificar(examen):
    """Ejecutar únicamente desde una transacción con bloqueo del examen."""
    if examen.estado == "FINALIZADO":
        raise ValueError("El simulacro ya fue calificado.")
    respuestas = examen.respuestas
    detalles = []
    for pregunta in examen.preguntas:
        seleccion = respuestas.get(str(pregunta["id"]), "")
        acierto = seleccion == pregunta["correcta"]
        detalles.append({**pregunta, "respuesta": seleccion, "acierto": acierto})
    aciertos = sum(int(p["acierto"]) for p in detalles)
    intento = IntentoEvaluacion.objects.create(
        estudiante=examen.estudiante,
        materia="Simulacro: Avanzado práctica",
        total_preguntas=len(detalles),
        aciertos=aciertos,
    )
    RespuestaEvaluacion.objects.bulk_create([
        RespuestaEvaluacion(
            intento=intento, numero=p["id"],
            competencia=(p["materia"] + " · " + p["competencia"])[:100],
            enunciado=p.get("contexto", ""), pregunta=p["pregunta"],
            opciones=p["opciones"], respuesta_estudiante=p["respuesta"],
            respuesta_correcta=p["correcta"], explicacion=p["explicacion"],
            es_correcta=p["acierto"],
        ) for p in detalles
    ])
    examen.intento = intento
    examen.estado = "FINALIZADO"
    examen.restantes_segundos = 0
    examen.finalizado_en = timezone.now()
    examen.save(update_fields=(
        "intento", "estado", "restantes_segundos",
        "finalizado_en", "actualizado_en",
    ))
    return examen


def resumen_resultados(examen):
    """Agrupar por área y competencia, sin inventar evidencia pedagógica."""
    cuentas = defaultdict(lambda: [0, 0])
    detalles = []
    for p in examen.preguntas:
        seleccion = examen.respuestas.get(str(p["id"]), "")
        correcto = seleccion == p["correcta"]
        cuentas[(p["materia"], p["competencia"])][0] += 1
        cuentas[(p["materia"], p["competencia"])][1] += int(correcto)
        detalles.append({
            "materia": p["materia"], "competencia": p["competencia"],
            "pregunta": p["pregunta"], "respuesta": seleccion,
            "correcta": p["correcta"], "explicacion": p["explicacion"],
            "acierto": correcto,
        })
    filas = [
        {"materia": materia, "competencia": competencia, "total": total,
         "aciertos": aciertos, "porcentaje": round(aciertos * 100 / total, 1)}
        for (materia, competencia), (total, aciertos) in sorted(cuentas.items())
    ]
    return filas, detalles
