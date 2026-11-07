"""Indicadores agregados: nunca se exponen identidades de estudiantes."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_GET

from Principal.models import PreguntaBanco
from Principal.services.calidad_preguntas import (
    consistencia_por_formulario, resumen_calidad,
)
from .banco_preguntas import puede_curaduría


@login_required
@require_GET
def calidad_banco(request):
    if not puede_curaduría(request.user):
        raise PermissionDenied("Solo la curaduría puede revisar las estadísticas.")
    materia = request.GET.get("materia", "")
    if materia not in dict(PreguntaBanco.MATERIAS):
        materia = ""
    return render(request, "CalidadPreguntas.html", {
        "materia": materia,
        "materias": PreguntaBanco.MATERIAS,
        "filas": resumen_calidad(materia),
        "consistencia": consistencia_por_formulario(),
    })
