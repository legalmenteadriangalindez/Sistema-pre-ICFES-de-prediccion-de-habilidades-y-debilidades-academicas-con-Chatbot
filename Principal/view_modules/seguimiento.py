"""Diagnóstico y persistencia del plan semanal propios del estudiante."""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Principal.models import PlanEstudioSemanal, SesionPlanSemanal
from Principal.services.seguimiento import plan_semanal, resumen_estudiante
from Principal.services.plan_persistente import (
    crear_plan_actual, historial_semanal, lunes_de, marcar_sesion,
    reabrir_sesion, resumen_plan,
)
from .selectores import _estudiante

@login_required
def diagnostico_academico(request):
    estudiante = _estudiante(request.user)
    if not estudiante:
        raise PermissionDenied("Esta información pertenece al perfil estudiantil.")
    resumen = resumen_estudiante(estudiante)
    return render(request, "DiagnosticoAcademico.html", {"resumen": resumen})


@login_required
@require_http_methods(["GET", "POST"])
def plan_estudio(request):
    """Guarda y mide sesiones del propio estudiante; las semanas viejas son solo lectura."""
    estudiante = _estudiante(request.user)
    if not estudiante:
        raise PermissionDenied("Esta planificación requiere un perfil estudiantil.")
    hoy = timezone.localdate()
    semana_actual = lunes_de(hoy)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "crear":
            _, creado = crear_plan_actual(estudiante, semana_actual)
            if creado:
                messages.success(request, "Tu plan de esta semana quedó guardado.")
            else:
                messages.info(request, "Ya tienes un plan guardado esta semana; se conservaron tus avances.")
            return redirect("plan_semanal")

        if accion in ("registrar", "reabrir"):
            sesion_id = request.POST.get("sesion_id", "")
            if not sesion_id.isdecimal():
                raise Http404("Sesión no encontrada.")
            with transaction.atomic():
                sesion = get_object_or_404(
                    SesionPlanSemanal.objects.select_for_update(),
                    pk=int(sesion_id),
                    plan__estudiante=estudiante,
                    plan__semana_inicio=semana_actual,
                )
                if accion == "registrar":
                    try:
                        minutos = int(request.POST.get("minutos", ""))
                    except (ValueError, TypeError):
                        messages.error(request, "Introduce una cantidad válida de minutos.")
                    else:
                        notas = request.POST.get("notas", "").strip()
                        try:
                            marcar_sesion(sesion, minutos, notas)
                        except ValueError as exc:
                            messages.error(request, str(exc))
                        else:
                            messages.success(request, "Sesión registrada. Tu progreso se actualizó.")
                else:
                    reabrir_sesion(sesion)
                    messages.info(request, "El registro se reabrió para corregirlo.")
            return redirect("plan_semanal")
        return HttpResponseBadRequest("Acción de planificación no válida.")

    semana_seleccionada = request.GET.get("semana")
    if semana_seleccionada:
        try:
            inicio = date.fromisoformat(semana_seleccionada)
        except ValueError:
            return HttpResponseBadRequest("Fecha de semana inválida.")
        if inicio.weekday() != 0:
            return HttpResponseBadRequest("La semana debe comenzar en lunes.")
    else:
        inicio = semana_actual

    plan_guardado = PlanEstudioSemanal.objects.filter(
        estudiante=estudiante, semana_inicio=inicio
    ).first()
    progreso = resumen_plan(plan_guardado) if plan_guardado else None
    resumen = resumen_estudiante(estudiante)
    es_actual = inicio == semana_actual
    return render(request, "PlanSemanal.html", {
        "resumen": resumen,
        "plan_guardado": plan_guardado,
        "progreso": progreso,
        "semana_inicio": inicio,
        "semana_fin": inicio + timedelta(days=6),
        "es_semana_actual": es_actual,
        "hoy": hoy,
        "propuesta": plan_semanal(resumen) if es_actual and not plan_guardado else [],
        "historial": historial_semanal(estudiante),
    })

