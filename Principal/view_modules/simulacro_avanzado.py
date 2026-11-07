"""Interfaz del simulacro avanzado; los intentos pertenecen solo al alumno."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from Principal.models import SimulacroAvanzado
from Principal.services.simulacro_persistente import (
    PREGUNTAS_POR_BLOQUE, actualizar, iniciar, obtener_activo,
    resumen_resultados, segundos_disponibles, sincronizar,
)
from .selectores import _estudiante


def datos_visibles(examen):
    """Nunca incluir en HTML claves, explicaciones ni otros bloques."""
    inicio = (examen.bloque - 1) * PREGUNTAS_POR_BLOQUE
    preguntas = []
    for p in examen.preguntas[inicio:inicio + PREGUNTAS_POR_BLOQUE]:
        preguntas.append({
            "id": p["id"], "materia": p["materia"],
            "competencia": p["competencia"], "contexto": p["contexto"],
            "pregunta": p["pregunta"], "opciones": p["opciones"],
            "respuesta": examen.respuestas.get(str(p["id"]), ""),
        })
    return preguntas


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def simulacro_avanzado(request):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        return render(request, "SimulacroAvanzado.html", {
            "error": "Necesitas un perfil estudiantil para realizar el simulacro."
        }, status=403)

    error = ""
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        try:
            if accion == "iniciar":
                iniciar(estudiante)
                return redirect("simulacro_avanzado")
            if accion == "guardar":
                raw = request.POST.get("indice", "")
                if not raw.isdecimal():
                    return JsonResponse({"error": "Índice inválido."}, status=400)
                examen = actualizar(
                    estudiante, "guardar", indice=int(raw),
                    valor=request.POST.get("valor", ""),
                )
                return JsonResponse({
                    "ok": True,
                    "respondidas": sum(
                        1 for x in examen.respuestas if (
                            (examen.bloque - 1) * PREGUNTAS_POR_BLOQUE
                            <= int(x) < examen.bloque * PREGUNTAS_POR_BLOQUE
                        )
                    ),
                })
            if accion in ("pausar", "reanudar", "siguiente_bloque", "finalizar"):
                examen = actualizar(estudiante, accion)
                if accion == "finalizar":
                    return redirect("resultado_simulacro_avanzado", examen_id=examen.pk)
                return redirect("simulacro_avanzado")
            error = "La acción solicitada no existe."
        except ValueError as exc:
            if accion == "guardar":
                return JsonResponse({"error": str(exc)}, status=400)
            error = str(exc)

    examen = obtener_activo(estudiante)
    if examen:
        sincronizar(examen)
    return render(request, "SimulacroAvanzado.html", {
        "error": error,
        "examen": examen,
        "preguntas": datos_visibles(examen) if examen else [],
        "restantes": segundos_disponibles(examen) if examen else 0,
        "total_bloques": 2,
    })


@login_required
@never_cache
@require_http_methods(["GET"])
def resultado_simulacro_avanzado(request, examen_id):
    estudiante = _estudiante(request.user)
    if not estudiante:
        return render(request, "SimulacroAvanzado.html", {}, status=403)
    examen = get_object_or_404(
        SimulacroAvanzado, pk=examen_id,
        estudiante=estudiante, estado="FINALIZADO",
    )
    filas, detalles = resumen_resultados(examen)
    return render(request, "ResultadoSimulacroAvanzado.html", {
        "examen": examen, "filas": filas, "detalles": detalles,
    })
