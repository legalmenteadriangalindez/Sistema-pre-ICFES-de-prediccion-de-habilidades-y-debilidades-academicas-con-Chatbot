"""Material aprobado y trazable para apoyar el tutor."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from Principal.models import PreguntaBanco, SimulacroAvanzado
from .selectores import _estudiante


@login_required
@require_GET
def material_validado(request, pregunta_id):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        raise PermissionDenied("Solo estudiantes pueden consultar este material.")
    if SimulacroAvanzado.objects.filter(
        estudiante=estudiante, estado__in=("EN_CURSO", "PAUSADO"),
    ).exists():
        raise PermissionDenied("El material se consulta fuera de simulacros activos.")
    pregunta = get_object_or_404(
        PreguntaBanco,
        pk=pregunta_id, estado="APROBADA", activo=True,
    )
    return render(request, "MaterialValidado.html", {"pregunta": pregunta})
