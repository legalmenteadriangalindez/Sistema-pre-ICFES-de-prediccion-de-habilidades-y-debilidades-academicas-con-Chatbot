"""Práctica adaptativa con claves únicamente en sesión BD y corrección en servidor."""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from Principal.services.banco_adaptativo import (
    preguntas_para_sesion, seleccionar_adaptativas,
)
from Principal.services.evaluaciones import (
    calificar_y_guardar_evaluacion, preguntas_para_estudiante,
)
from .selectores import _estudiante

SESION = "practica_adaptativa_activa"
DURACION = timedelta(minutes=30)


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def practica_adaptativa(request):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        return render(request, "PracticaAdaptativa.html", {
            "error": "Necesitas un perfil de estudiante para realizar esta práctica.",
        }, status=403)

    contexto = {}
    accion = request.POST.get("accion", "") if request.method == "POST" else ""
    sesion = request.session.get(SESION)

    if accion == "iniciar":
        # Una práctica iniciada sustituye a la pendiente, sin calificarla.
        preguntas, focos = seleccionar_adaptativas(estudiante)
        if not preguntas:
            request.session.pop(SESION, None)
            contexto["error"] = (
                "Todavía no hay preguntas revisadas y aprobadas. "
                "Puedes continuar con los cuestionarios y simulacros habituales."
            )
        else:
            sesion = {
                "user_id": request.user.pk,
                "estudiante_id": estudiante.pk,
                "preguntas": preguntas_para_sesion(preguntas),
                "vence": (timezone.now() + DURACION).timestamp(),
                "focos": focos,
            }
            request.session[SESION] = sesion
    elif accion == "calificar":
        # Nunca aceptar claves ni identificadores del banco enviados por el cliente.
        request.session.pop(SESION, None)
        if (
            not sesion or sesion["user_id"] != request.user.pk
            or sesion["estudiante_id"] != estudiante.pk
            or timezone.now().timestamp() > sesion["vence"]
        ):
            contexto["error"] = (
                "La práctica expiró, ya se calificó o pertenece a otra sesión. "
                "Inicia una nueva práctica."
            )
        else:
            resultado, detalles, competencias = calificar_y_guardar_evaluacion(
                estudiante=estudiante,
                materia="Práctica adaptativa",
                preguntas=sesion["preguntas"],
                datos_respuesta=request.POST,
            )
            contexto.update({
                "resultado": resultado,
                "detalles": detalles,
                "competencias": competencias,
            })
    elif request.method == "POST":
        contexto["error"] = "Acción de práctica no reconocida."

    activa = request.session.get(SESION)
    if activa and (
        activa["user_id"] != request.user.pk
        or activa["estudiante_id"] != estudiante.pk
        or timezone.now().timestamp() > activa["vence"]
    ):
        request.session.pop(SESION, None)
        activa = None
    if activa:
        contexto["preguntas"] = preguntas_para_estudiante(activa["preguntas"])
        contexto["focos"] = activa["focos"]
        contexto["vence"] = activa["vence"]
    return render(request, "PracticaAdaptativa.html", contexto)
