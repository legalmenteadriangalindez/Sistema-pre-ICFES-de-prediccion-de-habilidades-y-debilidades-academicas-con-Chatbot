"""Selectores de identidad y autorización por rol."""

from Principal.models import Estudiante, PerfilUsuario, Persona


def es_gestor(request_user):
    if not request_user.is_authenticated:
        return False
    if request_user.is_superuser:
        return True
    return PerfilUsuario.objects.filter(
        user=request_user, roles__nombre__iexact="ADMIN"
    ).exists()


def _tiene_rol(user, nombre):
    return user.is_authenticated and (
        user.is_superuser
        or PerfilUsuario.objects.filter(
            user=user, roles__nombre__iexact=nombre
        ).exists()
    )


def _estudiante(user):
    perfil = PerfilUsuario.objects.filter(user=user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    return Estudiante.objects.filter(persona=persona).first() if persona else None
