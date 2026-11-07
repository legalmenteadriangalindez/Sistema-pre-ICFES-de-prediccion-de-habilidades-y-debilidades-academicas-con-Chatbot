"""Autorización explícita del acudiente vinculado para el tutor IA."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from Principal.models import ConsentimientoTutorIA, EstudianteAcudiente
from Principal.services.privacidad_educativa import (
    es_menor, registrar_auditoria,
)
from .selectores import _tiene_rol


def vinculados(user):
    return EstudianteAcudiente.objects.filter(
        acudiente__persona__perfil_user__user=user,
    ).select_related("estudiante__persona")


@login_required
@require_http_methods(["GET", "POST"])
def consentimiento_tutor(request):
    if not _tiene_rol(request.user, "ACUDIENTE"):
        raise PermissionDenied("Esta autorización corresponde al acudiente vinculado.")
    if request.method == "POST":
        alumno = request.POST.get("estudiante", "")
        decision = request.POST.get("decision", "")
        if not alumno.isdecimal() or decision not in ("autorizar", "revocar"):
            raise PermissionDenied("Datos de consentimiento inválidos.")
        vinculo = get_object_or_404(vinculados(request.user), estudiante_id=int(alumno))
        estudiante = vinculo.estudiante
        if not es_menor(estudiante):
            messages.info(request, "Esta autorización solo corresponde a menores.")
        else:
            with transaction.atomic():
                registro, _ = ConsentimientoTutorIA.objects.select_for_update().get_or_create(
                    estudiante=estudiante,
                    defaults={"acudiente_usuario": request.user, "autorizado": False},
                )
                registro.acudiente_usuario = request.user
                registro.autorizado = decision == "autorizar"
                registro.save(update_fields=[
                    "acudiente_usuario", "autorizado", "actualizado_en",
                ])
                registrar_auditoria(
                    request.user, "TUTOR_IA_" + decision.upper(),
                    "ConsentimientoTutorIA", registro.pk,
                )
            messages.success(request, "Preferencia de uso del tutor IA actualizada.")
        return redirect("consentimiento_tutor")
    filas = []
    for vinculo in vinculados(request.user):
        alumno = vinculo.estudiante
        filas.append({
            "estudiante": alumno,
            "menor": es_menor(alumno),
            "autorizado": ConsentimientoTutorIA.objects.filter(
                estudiante=alumno, autorizado=True,
            ).exists(),
        })
    return render(request, "ConsentimientoTutor.html", {"filas": filas})
