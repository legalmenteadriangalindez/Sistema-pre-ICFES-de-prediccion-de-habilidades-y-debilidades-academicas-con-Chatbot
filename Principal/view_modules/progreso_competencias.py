"""Reportes de progreso: propio o de matrícula docente autorizada."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from Principal.services.analisis_progreso import comparar_progreso
from .docentes import matriculas_permitidas_docente
from .selectores import _estudiante, _tiene_rol


@login_required
@require_GET
def progreso_competencias(request):
    matricula_id = request.GET.get("matricula", "").strip()
    if matricula_id:
        if not _tiene_rol(request.user, "DOCENTE"):
            raise PermissionDenied("Solo el docente autorizado puede consultar esa matrícula.")
        if not matricula_id.isdecimal():
            raise PermissionDenied("Matrícula no válida.")
        matricula = get_object_or_404(
            matriculas_permitidas_docente(request.user).select_related(
                "estudiante__persona"
            ), pk=int(matricula_id),
        )
        estudiante = matricula.estudiante
        es_docente = True
    else:
        estudiante = _estudiante(request.user)
        if estudiante is None:
            raise PermissionDenied("Necesitas un perfil de estudiante.")
        es_docente = False
    return render(request, "ProgresoCompetencias.html", {
        "filas": comparar_progreso(estudiante),
        "es_docente": es_docente,
        "estudiante": estudiante,
    })
