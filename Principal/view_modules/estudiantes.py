"""Recomendaciones descriptivas y actividades propias del estudiante."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from Principal.models import (
    ActividadAsignada, AnalisisCognitivo, Estudiante, MaterialAsignado,
    Matricula, PerfilPedagogico, PerfilUsuario, Persona, RecomendacionVocacional,
)

@login_required
def recomendaciones(request):
    user = request.user

    perfil = PerfilUsuario.objects.filter(user= user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first()
    estudiante = Estudiante.objects.filter(persona= persona).first()

    if not estudiante:
        return render(request,"Recomendaciones.html",{"error": "este perfil no tiene estudiante asociado"})
    
    print(estudiante)
    matricula = Matricula.objects.filter(estudiante=estudiante,activa=True).first()
    perfil_pedagogico = None
    analisis_cognitivo = None
    recomendacion_vocacional = None
    material_estudio_recomendado = None

    perfil_pedagogico = PerfilPedagogico.objects.filter(estudiante=estudiante).first()
    analisis_cognitivo = AnalisisCognitivo.objects.filter(estudiante=estudiante).first()

    recomendacion_vocacional = RecomendacionVocacional.objects.filter(matricula=matricula)
    material_estudio_recomendado = MaterialAsignado.objects.filter(matricula=matricula)


    contexto = {
        "perfil_pedagogico": perfil_pedagogico,
        "analisis_cognitivo": analisis_cognitivo,
        "recomendacion_vocacional": recomendacion_vocacional,
        "material_estudio_recomendado": material_estudio_recomendado,
    }

    return render(request,"Recomendaciones.html",contexto)     # view recomendacion de carreras con IA
#********************************RECOMENDACIONES**************************************************



# =============================CARRERAS======================================


@login_required
def actividadesUsuario(request):
    perfil = PerfilUsuario.objects.filter(user=request.user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    estudiante = Estudiante.objects.filter(persona=persona).first() if persona else None
    matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).first() if estudiante else None
    if not matricula:
        return render(request, "actividadesUsuario.html", {
            "error": "No existe una matrícula activa asociada a esta cuenta.",
            "actividades": [], "total_actividades": 0, "total_completadas": 0
        })
    if request.method == "POST" and request.POST.get("marcar_completada"):
        identificador = request.POST.get("actividad_id")
        if identificador and identificador.isdigit():
            # Filtrar por la matrícula evita editar actividades de otros estudiantes.
            ActividadAsignada.objects.filter(
                pk=int(identificador), matricula=matricula
            ).update(completada=True)
        return redirect("actividadesUsuario")
    actividades = ActividadAsignada.objects.filter(matricula=matricula).select_related(
        "actividad__tema__materia", "actividad__nivel"
    ).order_by("-fecha_asignacion")
    return render(request, "actividadesUsuario.html", {
        "actividades": actividades,
        "total_actividades": actividades.count(),
        "total_completadas": actividades.filter(completada=True).count()
    })

