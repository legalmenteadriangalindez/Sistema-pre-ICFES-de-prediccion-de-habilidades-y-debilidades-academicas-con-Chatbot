"""Indicadores descriptivos por respuestas de evaluaciones; no es un modelo predictivo."""
from collections import defaultdict

from Principal.models import IntentoEvaluacion, RespuestaEvaluacion

AREAS_BASE = ("Matemáticas", "Lectura Crítica", "Sociales y Ciudadanas", "Ciencias Naturales", "Inglés")


def _materia(respuesta):
    """Recupera el área del simulacro integral sin atribuirlo a una sexta materia."""
    intento = respuesta.intento
    if intento.materia in ("Simulacro: Integral", "Simulacro: Integral ampliado", "Práctica adaptativa"):
        prefijo = respuesta.competencia.split(" · ", 1)[0]
        return prefijo if prefijo in AREAS_BASE else None
    if intento.materia.startswith("Simulacro: "):
        return intento.materia.partition(": ")[2]
    return intento.materia


def resumen_estudiante(estudiante):
    """Consulta solamente las evaluaciones del estudiante suministrado.

    El umbral de atención (<60%) es orientativo y no representa una probabilidad.
    """
    intentos = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("-fecha", "-pk")[:20])
    respuestas = RespuestaEvaluacion.objects.filter(intento__estudiante=estudiante).select_related("intento")
    conteos = defaultdict(lambda: [0, 0])
    competencias = defaultdict(lambda: [0, 0])
    for respuesta in respuestas:
        materia = _materia(respuesta)
        if not materia:
            continue
        conteos[materia][0] += 1
        conteos[materia][1] += int(respuesta.es_correcta)
        comp = respuesta.competencia.split(" · ", 1)[-1]
        competencias[(materia, comp)][0] += 1
        competencias[(materia, comp)][1] += int(respuesta.es_correcta)
    por_area = []
    for nombre in AREAS_BASE:
        total, aciertos = conteos.get(nombre, [0, 0])
        porcentaje = round(aciertos / total * 100, 1) if total else None
        por_area.append({"nombre": nombre, "total": total, "aciertos": aciertos,
                         "porcentaje": porcentaje,
                         "prioridad": "Practicar" if total >= 3 and porcentaje < 60 else "En seguimiento" if total else "Sin datos"})
    dificultades = [{"materia": m, "competencia": c, "total": t, "porcentaje": round(a * 100 / t, 1)}
                    for (m, c), (t, a) in competencias.items() if t >= 2 and a / t < 0.6]
    dificultades.sort(key=lambda d: (d["porcentaje"], -d["total"]))
    total_intentos = len(intentos)
    return {"areas": por_area, "dificultades": dificultades[:8], "intentos": intentos,
            "total_intentos": total_intentos, "con_datos": bool(conteos)}


def plan_semanal(resumen):
    """Siete propuestas reproducibles basadas en áreas medidas; sin datos usa rotación general."""
    areas = sorted(resumen["areas"], key=lambda a: (a["porcentaje"] is None, a["porcentaje"] if a["porcentaje"] is not None else 101))
    enfoque = [a["nombre"] for a in areas if a["total"] >= 3]
    if not enfoque:
        enfoque = list(AREAS_BASE)
    nombres = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    acciones = ("Practica ejercicios de", "Revisa errores de", "Refuerza conceptos de", "Resuelve un cuestionario de",
                "Explica con tus palabras temas de", "Realiza un simulacro de", "Descansa o repasa suavemente")
    plan = []
    for i, dia in enumerate(nombres):
        area = enfoque[i % len(enfoque)]
        texto = acciones[i] + (" " + area if i < 6 else "")
        plan.append({"dia": dia, "actividad": texto, "area": area,
                     "minutos": 20 if i == 6 else 45 if i == 5 else 30,
                     "link": "simulacros" if i == 5 else "test"})
    return plan
