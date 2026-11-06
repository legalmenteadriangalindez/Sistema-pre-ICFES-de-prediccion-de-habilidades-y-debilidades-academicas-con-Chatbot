"""Fachada pública de portales académicos (URLs, tests y módulos antiguos).

Implementaciones separadas en Principal.view_modules; conservar importaciones
históricas evita cambios en rutas y referencias de los otros controladores.
"""
from django.utils import timezone  # Alias usado por tests de fecha semanal.

from .view_modules.selectores import _estudiante, _matricula, _tiene_rol
from .view_modules.vocacional import orientacion_vocacional, comparador_carreras
from .view_modules.seguimiento import diagnostico_academico, plan_estudio
from .view_modules.docentes import matriculas_permitidas_docente, panel_docente
from .view_modules.acudientes import panel_acudiente

__all__ = [
    "_estudiante", "_matricula", "_tiene_rol",
    "orientacion_vocacional", "comparador_carreras",
    "diagnostico_academico", "plan_estudio",
    "matriculas_permitidas_docente", "panel_docente", "panel_acudiente",
]
