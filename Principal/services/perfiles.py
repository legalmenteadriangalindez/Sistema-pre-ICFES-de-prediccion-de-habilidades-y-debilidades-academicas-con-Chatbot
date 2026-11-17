"""Servicios de dominio para consultar y actualizar el perfil propio."""

from django.db import transaction

from Principal.models import Estudiante, Persona
from Principal.profile_forms import (
    EstudianteProfileUpdateForm,
    PersonaProfileUpdateForm,
    UserProfileUpdateForm,
)


def obtener_relaciones_perfil(user):
    """Devuelve la persona y el estudiante vinculados al usuario recibido."""

    persona = (
        Persona.objects.filter(perfil_user__user=user)
        .select_related("sexo")
        .first()
    )
    estudiante = (
        Estudiante.objects.filter(persona=persona).first() if persona else None
    )
    return persona, estudiante


def construir_formularios_perfil(data=None, *, user, persona=None, estudiante=None):
    """Construye los formularios independientes del perfil."""

    kwargs = {"data": data} if data is not None else {}
    return (
        UserProfileUpdateForm(instance=user, **kwargs),
        PersonaProfileUpdateForm(instance=persona, **kwargs) if persona else None,
        (
            EstudianteProfileUpdateForm(instance=estudiante, **kwargs)
            if estudiante
            else None
        ),
    )


@transaction.atomic
def guardar_perfil(user_form, persona_form=None, estudiante_form=None):
    """Guarda la cuenta y sus relaciones dentro de una única transacción."""

    user_form.save()
    if persona_form is not None:
        persona_form.save()
    if estudiante_form is not None:
        estudiante_form.save()
