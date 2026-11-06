"""Fachada pública de vistas administrativas.

Las operaciones y permisos están separados en Principal.view_modules.
Se preservan nombres usados en URLs y en imports existentes.
"""
from .view_modules.selectores import es_gestor
from .view_modules.admin_docentes import gestion_docentes
from .view_modules.admin_usuarios import gestion_users, eliminar_gestion_users
from .view_modules.admin_catalogos import (
    gestion_db, eliminar_admin_gestion_db,
    gestion_academica, eliminar_gestion_academica,
)
from .view_modules.admin_matriculas import (
    gestion_acudientes_estudiantes, eliminar_gestion_acudientes_estudiantes,
)
from .view_modules.acudientes import acudiente

__all__ = [
    "es_gestor", "gestion_docentes", "gestion_users", "eliminar_gestion_users",
    "gestion_db", "eliminar_admin_gestion_db",
    "gestion_academica", "eliminar_gestion_academica",
    "gestion_acudientes_estudiantes", "eliminar_gestion_acudientes_estudiantes",
    "acudiente",
]
