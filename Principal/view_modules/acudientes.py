"""Seguimiento familiar basado únicamente en vínculos formales."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils import timezone

from Principal.models import (
    ActividadAsignada, EstudianteAcudiente, IntentoEvaluacion, Matricula,
    PlanEstudioSemanal,
)
from Principal.services.plan_persistente import lunes_de, resumen_plan
from .selectores import _tiene_rol

@login_required
def panel_acudiente(request):
    if not _tiene_rol(request.user, "ACUDIENTE"):
        raise PermissionDenied("Necesitas el rol ACUDIENTE para consultar estudiantes vinculados.")
    # No mostrar un solo estudiante ajeno: se consulta la vinculación formal.
    vinculos = EstudianteAcudiente.objects.filter(
        acudiente__persona__perfil_user__user=request.user
    ).select_related("estudiante__persona", "relacion").order_by("estudiante__persona__apellido")
    hijos = []
    for vinculo in vinculos:
        estudiante = vinculo.estudiante
        matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).select_related(
            "curso__grado", "anio_lectivo"
        ).first()
        resultados = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("-fecha", "-pk")[:5])
        plan_de_la_semana = PlanEstudioSemanal.objects.filter(
            estudiante=estudiante, semana_inicio=lunes_de(timezone.localdate())
        ).first()
        hijos.append({"estudiante": estudiante, "matricula": matricula,
                     "relacion": vinculo.relacion, "resultados": resultados,
                     "plan_semanal": resumen_plan(plan_de_la_semana) if plan_de_la_semana else None,
                     "actividades_pendientes": ActividadAsignada.objects.filter(
                         matricula=matricula, completada=False
                     ).count() if matricula else 0})
    return render(request, "PanelAcudiente.html", {"hijos": hijos})

@login_required # @user_passes_test(es_coordinador)
def acudiente(request):
    
    contexto = {
        "acudientes": None,
        "estudiantes": None
    }
    return render(request, "acudiente.html", contexto)

