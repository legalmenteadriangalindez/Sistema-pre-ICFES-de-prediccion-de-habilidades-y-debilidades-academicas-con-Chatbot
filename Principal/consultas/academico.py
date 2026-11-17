"""Selectores de datos académicos reutilizables."""

from Principal.models import Matricula


def _matricula(estudiante):
    return (
        Matricula.objects.filter(estudiante=estudiante, activa=True).first()
        if estudiante
        else None
    )
