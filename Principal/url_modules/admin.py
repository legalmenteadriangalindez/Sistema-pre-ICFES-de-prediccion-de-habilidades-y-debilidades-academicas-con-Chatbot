"""Rutas de administración y gestión escolar."""

from django.urls import path

from Principal import views
from Principal.view_modules import admin_escolar, admin_operaciones
from Principal.view_modules import (
    admin_catalogos,
    admin_docentes,
    admin_matriculas,
    import_export,
)

urlpatterns = [
    path(
        "gestion/matriculas/importar/",
        import_export.cargar_matriculas,
        name="cargar_matriculas",
    ),
    path(
        "gestion/matriculas/plantilla/",
        import_export.descargar_plantilla_matriculas,
        name="descargar_plantilla_matriculas",
    ),
    path(
        "gestion/reportes/exportar/",
        import_export.exportar_reporte_matriculas,
        name="exportar_reporte_matriculas",
    ),
    path(
        "gestion/usuarios/<int:usuario_id>/editar/",
        admin_operaciones.editar_usuario,
        name="admin_editar_usuario",
    ),
    path(
        "gestion/personas/<int:persona_id>/editar/",
        admin_operaciones.editar_persona,
        name="admin_editar_persona",
    ),
    path(
        "gestion/estudiantes/<int:estudiante_id>/editar/",
        admin_operaciones.editar_necesidades_estudiante,
        name="admin_editar_necesidades_estudiante",
    ),
    path(
        "gestion/catalogos/<str:tipo>/<int:registro_id>/editar/",
        admin_operaciones.editar_catalogo,
        name="admin_editar_catalogo",
    ),
    path(
        "gestion/matriculas/",
        admin_escolar.gestion_matriculas_familias,
        name="admin_matriculas_familias",
    ),
    path(
        "gestion/matriculas/<int:matricula_id>/editar/",
        admin_escolar.editar_matricula,
        name="admin_editar_matricula",
    ),
    path(
        "gestion/vinculos/<int:vinculo_id>/editar/",
        admin_escolar.editar_vinculo_familiar,
        name="admin_editar_vinculo",
    ),
    path(
        "gestion/vinculos/<int:vinculo_id>/desvincular/",
        admin_escolar.desvincular_familiar,
        name="admin_desvincular_familiar",
    ),
    path(
        "gestion/reportes/",
        admin_escolar.reportes_academicos_admin,
        name="admin_reportes_academicos",
    ),
    path(
        "gestion/asignaciones-docentes/",
        admin_docentes.gestion_docentes,
        name="admin_asignaciones_docentes",
    ),
    path(
        "gestion_acudientes_estudiantes/",
        admin_matriculas.gestion_acudientes_estudiantes,
        name="gestion_acudientes_estudiantes",
    ),
    path("admin_gestion_users/", views.gestion_users, name="admin_gestion_users"),
    path(
        "admin_gestion_academica/",
        views.gestion_academica,
        name="admin_gestion_academica",
    ),
    path("admin_gestion_db/", views.gestion_db, name="admin_gestion_db"),
    path(
        "eliminar_admin_gestion_db/<tipo>/<id>",
        views.eliminar_admin_gestion_db,
        name="eliminar_admin_gestion_db",
    ),
    path(
        "eliminar_admin_gestion_academico/<tipo>/<id>",
        views.eliminar_gestion_academica,
        name="eliminar_admin_gestion_academico",
    ),
    path(
        "eliminar_admin_gestion_users/<tipo>/<id>",
        views.eliminar_gestion_users,
        name="eliminar_admin_gestion_users",
    ),
    path(
        "eliminar_gestion_acudientes_estudiantes/<tipo>/<id>",
        views.eliminar_gestion_acudientes_estudiantes,
        name="eliminar_gestion_acudientes_estudiantes",
    ),
]
