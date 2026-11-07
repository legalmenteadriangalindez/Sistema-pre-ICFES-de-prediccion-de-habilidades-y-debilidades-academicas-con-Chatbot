"""Agenda privada de repaso, sin claves visibles antes de responder."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_GET

from Principal.models import RepasoEspaciado
from Principal.services.repasos_espaciados import repasos_pendientes
from .selectores import _estudiante


@login_required
@require_GET
def agenda_repasos(request):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        raise PermissionDenied("Solo el estudiante puede consultar su agenda.")
    pendientes = list(repasos_pendientes(estudiante, limite=50))
    proximos = RepasoEspaciado.objects.filter(
        estudiante=estudiante, pregunta__estado="APROBADA", pregunta__activo=True,
    ).select_related("pregunta").order_by("proximo_repaso")[:50]
    return render(request, "AgendaRepasos.html", {
        "pendientes": pendientes,
        "proximos": proximos,
    })
