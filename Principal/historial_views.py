"""Historial de evaluaciones del estudiante autenticado."""
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Principal.models import Estudiante, IntentoEvaluacion, Persona, PerfilUsuario


@login_required
def historial_academico(request):
    perfil = PerfilUsuario.objects.filter(user=request.user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    estudiante = Estudiante.objects.filter(persona=persona).first() if persona else None
    if not estudiante:
        return render(request, "historial_academico.html", {"sin_perfil": True})

    intentos = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("fecha", "pk"))
    por_materia = defaultdict(list)
    for intento in intentos:
        por_materia[intento.materia].append(intento)

    series = []
    for materia, registros in sorted(por_materia.items()):
        puntos = []
        anterior = None
        for intento in registros:
            porcentaje = intento.porcentaje
            cambio = round(porcentaje - anterior, 1) if anterior is not None else None
            tendencia = ("Mejorando" if cambio > 0 else "Empeorando" if cambio < 0 else "Estable") if cambio is not None else "Primera evaluación"
            puntos.append({
                "fecha": intento.fecha, "porcentaje": porcentaje,
                "aciertos": intento.aciertos, "total": intento.total_preguntas,
                "cambio": cambio, "tendencia": tendencia,
            })
            anterior = porcentaje
        series.append({"materia": materia, "puntos": list(reversed(puntos)), "ultima": puntos[-1]})
    return render(request, "historial_academico.html", {"series": series, "total_intentos": len(intentos)})
