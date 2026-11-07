"""Planes formativos individualizados, permisos por matrícula y evaluación final."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from Principal.forms_intervencion import IntervencionForm
from Principal.models import IntervencionAcademica, Matricula
from Principal.services.seguimiento_intervenciones import contar_evidencias
from Principal.services.avisos_academicos import emitir_aviso
from .docentes import matriculas_permitidas_docente
from .selectores import _estudiante, _tiene_rol


@login_required
@require_http_methods(["GET", "POST"])
def intervenciones_docente(request):
    if not _tiene_rol(request.user, "DOCENTE"):
        raise PermissionDenied("Necesitas ser docente para diseñar intervenciones.")
    permitidas = matriculas_permitidas_docente(request.user)
    formulario = IntervencionForm(
        request.POST if request.method == "POST" else None,
        permitidas=permitidas,
    )
    if request.method == "POST" and formulario.is_valid():
        intervencion = formulario.save(commit=False)
        intervencion.docente = request.user
        # La medición de referencia queda congelada al crear el plan.
        ahora = timezone.now()
        intervencion.creado_en = ahora
        aciertos, total = contar_evidencias(
            intervencion.matricula.estudiante, intervencion.materia,
            intervencion.competencia, antes_de=ahora,
        )
        if total >= 2:
            intervencion.aciertos_inicial = aciertos
            intervencion.total_inicial = total
        intervencion.save()
        emitir_aviso(
            intervencion.matricula.estudiante.persona.perfil_user.user,
            "INTERVENCION", "Nuevo plan de recuperación",
            "Tu docente registró un plan de refuerzo. Consúltalo en Mis intervenciones.",
            f"intervencion-{intervencion.pk}",
        )
        messages.success(request, "Plan de intervención asignado al estudiante.")
        return redirect("intervenciones_docente")

    intervenciones = IntervencionAcademica.objects.filter(
        docente=request.user, matricula__in=permitidas,
    ).select_related(
        "matricula__estudiante__persona", "matricula__curso",
    )[:100]
    return render(request, "IntervencionesDocente.html", {
        "formulario": formulario, "intervenciones": intervenciones,
    })


@login_required
@require_POST
def cerrar_intervencion_docente(request, intervencion_id):
    if not _tiene_rol(request.user, "DOCENTE"):
        raise PermissionDenied("Necesitas ser docente.")
    observacion = request.POST.get("observacion", "").strip()
    if not 10 <= len(observacion) <= 2000:
        messages.error(request, "Explica el cierre con 10 a 2000 caracteres.")
        return redirect("intervenciones_docente")
    with transaction.atomic():
        intervencion = get_object_or_404(
            IntervencionAcademica.objects.select_for_update().filter(
                docente=request.user,
                matricula__in=matriculas_permitidas_docente(request.user),
            ), pk=intervencion_id,
        )
        if intervencion.estado != "ACTIVA":
            raise PermissionDenied("Este plan ya está cerrado.")
        aciertos, total = contar_evidencias(
            intervencion.matricula.estudiante, intervencion.materia,
            intervencion.competencia, despues_de=intervencion.creado_en,
        )
        intervencion.aciertos_final = aciertos if total >= 2 else None
        intervencion.total_final = total if total >= 2 else None
        intervencion.observacion_cierre = observacion
        intervencion.estado = "CERRADA"
        intervencion.cerrado_en = timezone.now()
        intervencion.save(update_fields=(
            "aciertos_final", "total_final", "observacion_cierre",
            "estado", "cerrado_en",
        ))
    messages.success(request, "Intervención cerrada; resultados descriptivos registrados.")
    return redirect("intervenciones_docente")


@login_required
@require_http_methods(["GET"])
def mis_intervenciones(request):
    estudiante = _estudiante(request.user)
    if estudiante is None:
        raise PermissionDenied("Necesitas un perfil de estudiante.")
    matriculas = Matricula.objects.filter(estudiante=estudiante)
    planes = IntervencionAcademica.objects.filter(
        matricula__in=matriculas,
    ).select_related("docente", "matricula__curso")[:100]
    return render(request, "MisIntervenciones.html", {"planes": planes})
