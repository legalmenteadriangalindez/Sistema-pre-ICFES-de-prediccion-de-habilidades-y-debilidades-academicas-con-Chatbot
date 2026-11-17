"""Vistas de perfil y preferencias de presentación.

La edición de cuenta solo trabaja con el usuario autenticado. Las relaciones
con Persona y Estudiante se resuelven por consultas explícitas para no depender
de excepciones de relaciones inversas ausentes.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from Principal.models import (
    Estudiante,
    EstudianteAcudiente,
    Matricula,
    PerfilUsuario,
    Persona,
)
from Principal.services.perfiles import (
    construir_formularios_perfil,
    guardar_perfil,
    obtener_relaciones_perfil,
)


@login_required
def configuraciones(request):
    return render(request, "Configuraciones.html")


@login_required
def perfil(request):
    perfil_usuario = PerfilUsuario.objects.filter(user=request.user).first()
    persona = (
        Persona.objects.filter(perfil_user=perfil_usuario)
        .select_related("sexo")
        .first()
        if perfil_usuario
        else None
    )
    estudiante = (
        Estudiante.objects.filter(persona=persona).first() if persona else None
    )
    matricula = (
        Matricula.objects.filter(estudiante=estudiante, activa=True)
        .select_related("curso__grado", "anio_lectivo")
        .first()
        if estudiante
        else None
    )
    vinculos = (
        EstudianteAcudiente.objects.filter(estudiante=estudiante).select_related(
            "acudiente__persona", "relacion"
        )
        if estudiante
        else EstudianteAcudiente.objects.none()
    )
    return render(
        request,
        "PerfilDeUsuarios.html",
        {
            "persona": persona,
            "estudiante": estudiante,
            "matricula": matricula,
            "vinculos": vinculos,
            "perfil_usuario": perfil_usuario,
        },
    )



@login_required
@require_http_methods(["GET", "POST"])
def editarPerfil(request: HttpRequest) -> HttpResponse:
    """Actualiza cuenta, datos personales y apoyos del propio usuario."""

    persona, estudiante = obtener_relaciones_perfil(request.user)

    if request.method == "POST":
        user_form, persona_form, estudiante_form = construir_formularios_perfil(
            request.POST,
            user=request.user,
            persona=persona,
            estudiante=estudiante,
        )

        user_valid = user_form.is_valid()
        persona_valid = persona_form is None or persona_form.is_valid()
        estudiante_valid = estudiante_form is None or estudiante_form.is_valid()

        if user_valid and persona_valid and estudiante_valid:
            guardar_perfil(user_form, persona_form, estudiante_form)
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("perfil")
    else:
        user_form, persona_form, estudiante_form = construir_formularios_perfil(
            user=request.user,
            persona=persona,
            estudiante=estudiante,
        )

    return render(
        request,
        "PerfilEditar.html",
        {
            "user_form": user_form,
            "persona_form": persona_form,
            "estudiante_form": estudiante_form,
            "estudiante": estudiante,
        },
    )
