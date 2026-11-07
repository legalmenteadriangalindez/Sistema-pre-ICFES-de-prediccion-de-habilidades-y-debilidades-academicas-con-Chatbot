"""Versiones auditables: ninguna edición modifica el texto ya respondido."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from Principal.models import PreguntaBanco
from .banco_preguntas import puede_curaduría
from .selectores import es_gestor


@login_required
@require_POST
def crear_revision_banco(request, pregunta_id):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes permiso para versionar preguntas.")
    with transaction.atomic():
        original = get_object_or_404(
            PreguntaBanco.objects.select_for_update(), pk=pregunta_id,
        )
        if original.estado != "APROBADA" or not original.activo:
            raise PermissionDenied("Solo se puede versionar la versión aprobada vigente.")
        if original.creado_por_id != request.user.pk and not es_gestor(request.user):
            raise PermissionDenied("Solo el autor o administración puede proponer una revisión.")
        raiz = original.revision_de or original
        # Bloquear la raíz para serializar números de versión entre peticiones.
        PreguntaBanco.objects.select_for_update().get(pk=raiz.pk)
        ultimo = PreguntaBanco.objects.filter(revision_de=raiz).aggregate(
            mayor=Max("numero_version")
        )["mayor"] or 1
        nueva = PreguntaBanco(
            revision_de=raiz,
            numero_version=ultimo + 1,
            materia=original.materia,
            competencia=original.competencia,
            evidencia=original.evidencia,
            dificultad=original.dificultad,
            contexto=original.contexto,
            enunciado=original.enunciado,
            opciones=dict(original.opciones),
            respuesta_correcta=original.respuesta_correcta,
            explicacion=original.explicacion,
            origen="DOCENTE", creado_por=request.user,
            estado="BORRADOR", activo=True,
        )
        nueva.full_clean()
        try:
            nueva.save()
        except IntegrityError:
            messages.error(request, "Se creó otra versión simultánea. Intenta de nuevo.")
            return redirect("banco_preguntas")
    messages.success(request, "Borrador de nueva versión creado. Debe pasar otra revisión.")
    return redirect("editar_pregunta_banco", pregunta_id=nueva.pk)


@login_required
@require_http_methods(["GET"])
def historial_versiones_banco(request, pregunta_id):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes permiso para consultar claves del banco.")
    original = get_object_or_404(PreguntaBanco, pk=pregunta_id)
    raiz = original.revision_de or original
    versiones = [raiz, *PreguntaBanco.objects.filter(
        revision_de=raiz
    ).select_related("creado_por", "revisado_por").order_by("numero_version")]
    return render(request, "HistorialVersionesBanco.html", {
        "raiz": raiz, "versiones": versiones,
    })
