"""Fachada de selectores de consultas y permisos compartidos.

Las vistas históricas siguen importando desde este módulo; las consultas viven
en `Principal.consultas` por dominio.
"""

from Principal.consultas.academico import _matricula
from Principal.consultas.identidad import _estudiante, _tiene_rol, es_gestor

__all__ = ("es_gestor", "_tiene_rol", "_estudiante", "_matricula")
