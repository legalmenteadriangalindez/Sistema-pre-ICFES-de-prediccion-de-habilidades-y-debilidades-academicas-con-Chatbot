"""Rutas del portal académico, prácticas y privacidad."""

from django.urls import path

from Principal import portal_academico, prediction_views, privacy_views
from Principal.historial_views import historial_academico
from Principal.simulacros_views import simulacros
from Principal.view_modules import (
    banco_preguntas as banco_ops,
    calidad_banco,
    docente_ops,
    intervenciones,
    material_validado,
    progreso_competencias,
    repasos,
    simulacro_avanzado,
    versiones_banco,
)
from Principal.view_modules import practica_adaptativa as adaptativo_ops
from Principal.view_modules import avisos, consentimientos, import_export

urlpatterns = [
    path("repasos/", repasos.agenda_repasos, name="agenda_repasos"),
    path(
        "progreso-competencias/",
        progreso_competencias.progreso_competencias,
        name="progreso_competencias",
    ),
    path(
        "material-validado/<int:pregunta_id>/",
        material_validado.material_validado,
        name="material_validado",
    ),
    path(
        "privacidad/consentimiento-ia/",
        consentimientos.consentimiento_tutor,
        name="consentimiento_tutor",
    ),
    path("avisos/", avisos.mis_avisos, name="mis_avisos"),
    path(
        "avisos/<int:aviso_id>/leido/",
        avisos.marcar_aviso_leido,
        name="marcar_aviso_leido",
    ),
    path(
        "simulacros/avanzado/",
        simulacro_avanzado.simulacro_avanzado,
        name="simulacro_avanzado",
    ),
    path(
        "simulacros/avanzado/resultado/<int:examen_id>/",
        simulacro_avanzado.resultado_simulacro_avanzado,
        name="resultado_simulacro_avanzado",
    ),
    path("banco-preguntas/calidad/", calidad_banco.calidad_banco, name="calidad_banco"),
    path(
        "banco-preguntas/<int:pregunta_id>/nueva-version/",
        versiones_banco.crear_revision_banco,
        name="crear_revision_banco",
    ),
    path(
        "banco-preguntas/<int:pregunta_id>/historial/",
        versiones_banco.historial_versiones_banco,
        name="historial_versiones_banco",
    ),
    path(
        "panel-docente/intervenciones/",
        intervenciones.intervenciones_docente,
        name="intervenciones_docente",
    ),
    path(
        "panel-docente/intervenciones/<int:intervencion_id>/cerrar/",
        intervenciones.cerrar_intervencion_docente,
        name="cerrar_intervencion_docente",
    ),
    path(
        "intervenciones/mias/",
        intervenciones.mis_intervenciones,
        name="mis_intervenciones",
    ),
    path("banco-preguntas/", banco_ops.banco_preguntas, name="banco_preguntas"),
    path(
        "banco-preguntas/<int:pregunta_id>/editar/",
        banco_ops.editar_pregunta_banco,
        name="editar_pregunta_banco",
    ),
    path(
        "banco-preguntas/<int:pregunta_id>/enviar/",
        banco_ops.enviar_pregunta_revision,
        name="enviar_pregunta_revision",
    ),
    path(
        "banco-preguntas/<int:pregunta_id>/revisar/",
        banco_ops.revisar_pregunta_banco,
        name="revisar_pregunta_banco",
    ),
    path(
        "practica-adaptativa/",
        adaptativo_ops.practica_adaptativa,
        name="practica_adaptativa",
    ),
    path(
        "panel-docente/actividad/<int:actividad_id>/editar/",
        docente_ops.editar_actividad_docente,
        name="editar_actividad_docente",
    ),
    path(
        "panel-docente/estudiante/<int:matricula_id>/",
        docente_ops.detalle_estudiante_docente,
        name="detalle_estudiante_docente",
    ),
    path("historial-academico/", historial_academico, name="historial_academico"),
    path("simulacros/", simulacros, name="simulacros"),
    path(
        "orientacion-vocacional/",
        portal_academico.orientacion_vocacional,
        name="orientacion_vocacional",
    ),
    path("plan-semanal/", portal_academico.plan_estudio, name="plan_semanal"),
    path(
        "diagnostico-academico/",
        portal_academico.diagnostico_academico,
        name="diagnostico_academico",
    ),
    path(
        "prediccion-academica/",
        prediction_views.prediccion_estudiante,
        name="prediccion_estudiante",
    ),
    path(
        "gestion/validacion-prediccion/",
        prediction_views.validacion_prediccion,
        name="validacion_prediccion",
    ),
    path("panel-docente/", portal_academico.panel_docente, name="panel_docente"),
    path("privacidad/", privacy_views.privacidad, name="privacidad"),
    path(
        "privacidad/exportar/",
        privacy_views.exportar_mis_datos,
        name="exportar_mis_datos",
    ),
]
