"""Vistas de predicción responsable; resultados de cada estudiante son privados."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .management_views import es_gestor
from .portal_academico import _estudiante
from .services.prediccion_academica import (
    auditar_datos, cargar_modelo, predicciones_estudiante,
)


@login_required
@never_cache
@require_GET
def prediccion_estudiante(request):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        raise PermissionDenied("La predicción requiere un perfil de estudiante.")
    modelo = cargar_modelo()
    predicciones = predicciones_estudiante(estudiante, modelo=modelo) if modelo else []
    return render(request, "PrediccionAcademica.html", {
        "modelo": modelo,
        "predicciones": predicciones,
        "sin_modelo": modelo is None,
        "sin_historia": bool(modelo) and not predicciones,
    })


@login_required
@never_cache
@require_GET
def validacion_prediccion(request):
    if not es_gestor(request.user):
        raise PermissionDenied("Solo un administrador puede revisar el entrenamiento.")
    modelo = cargar_modelo()
    return render(request, "ValidacionPrediccion.html", {
        "auditoria_actual": auditar_datos(),
        "modelo": modelo,
        "evaluacion": modelo.get("evaluacion") if modelo else None,
    })
