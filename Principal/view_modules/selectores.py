"""Selectores y permisos compartidos por los portales y paneles administrativos.

Estos helpers mantienen las mismas reglas que los controladores previos.
"""
from django.db.models import Q

from Principal.models import (
    AsignacionDocenteCurso, Estudiante, Matricula, PerfilUsuario, Persona,
)

def es_gestor(request_user):
    if not request_user.is_authenticated:
        return False
    if request_user.is_superuser:
        return True
    return PerfilUsuario.objects.filter(
        user=request_user, roles__nombre__iexact="ADMIN"
    ).exists()

def _tiene_rol(user, nombre):
    return user.is_authenticated and (user.is_superuser or PerfilUsuario.objects.filter(
        user=user, roles__nombre__iexact=nombre
    ).exists())


def _estudiante(user):
    perfil = PerfilUsuario.objects.filter(user=user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    return Estudiante.objects.filter(persona=persona).first() if persona else None


def _matricula(estudiante):
    return Matricula.objects.filter(estudiante=estudiante, activa=True).first() if estudiante else None

