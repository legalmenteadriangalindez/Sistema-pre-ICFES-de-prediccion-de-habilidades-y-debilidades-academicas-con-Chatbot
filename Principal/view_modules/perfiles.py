"""Vistas de perfil y preferencias de presentación.

La edición de cuenta solo trabaja con el usuario autenticado. Las relaciones
con Persona y Estudiante se resuelven por consultas explícitas para no depender
de excepciones de relaciones inversas ausentes.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
from Principal.profile_forms import (
    EstudianteProfileUpdateForm,
    PersonaProfileUpdateForm,
    UserProfileUpdateForm,
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


def _persona_del_usuario(user):
    """Obtiene únicamente la persona vinculada al usuario autenticado."""

    return (
        Persona.objects.filter(perfil_user__user=user)
        .select_related("sexo")
        .first()
    )


def _estudiante_de_persona(persona):
    if persona is None:
        return None
    return Estudiante.objects.filter(persona=persona).first()


@login_required
@require_http_methods(["GET", "POST"])
def editarPerfil(request: HttpRequest) -> HttpResponse:
    """Actualiza cuenta, datos personales y apoyos del propio usuario."""

    persona = _persona_del_usuario(request.user)
    estudiante = _estudiante_de_persona(persona)

    if request.method == "POST":
        user_form = UserProfileUpdateForm(request.POST, instance=request.user)
        persona_form = (
            PersonaProfileUpdateForm(request.POST, instance=persona)
            if persona
            else None
        )
        estudiante_form = (
            EstudianteProfileUpdateForm(request.POST, instance=estudiante)
            if estudiante
            else None
        )

        user_valid = user_form.is_valid()
        persona_valid = persona_form is None or persona_form.is_valid()
        estudiante_valid = estudiante_form is None or estudiante_form.is_valid()

        if user_valid and persona_valid and estudiante_valid:
            with transaction.atomic():
                user_form.save()
                if persona_form is not None:
                    persona_form.save()
                if estudiante_form is not None:
                    estudiante_form.save()
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("perfil")
    else:
        user_form = UserProfileUpdateForm(instance=request.user)
        persona_form = (
            PersonaProfileUpdateForm(instance=persona) if persona else None
        )
        estudiante_form = (
            EstudianteProfileUpdateForm(instance=estudiante)
            if estudiante
            else None
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
