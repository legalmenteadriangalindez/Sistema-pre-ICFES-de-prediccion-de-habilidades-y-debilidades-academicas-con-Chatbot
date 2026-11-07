from django.urls import path
from . import portal_academico, privacy_views, prediction_views
from . import views # import de la vista
from .simulacros_views import simulacros
from .historial_views import historial_academico 
from django.urls import path, include  # librerias nesesarias para hacer la referencia desde url.py del proyecto
from .view_modules import docentes as docente_ops, admin_operaciones, admin_escolar
from .view_modules import banco_preguntas as banco_ops, practica_adaptativa as adaptativo_ops
from .view_modules import (calidad_banco, intervenciones, simulacro_avanzado, versiones_banco) 

urlpatterns = [
  path("simulacros/avanzado/", simulacro_avanzado.simulacro_avanzado, name="simulacro_avanzado"),
  path("simulacros/avanzado/resultado/<int:examen_id>/", simulacro_avanzado.resultado_simulacro_avanzado, name="resultado_simulacro_avanzado"),
  path("banco-preguntas/calidad/", calidad_banco.calidad_banco, name="calidad_banco"),
  path("banco-preguntas/<int:pregunta_id>/nueva-version/", versiones_banco.crear_revision_banco, name="crear_revision_banco"),
  path("banco-preguntas/<int:pregunta_id>/historial/", versiones_banco.historial_versiones_banco, name="historial_versiones_banco"),
  path("panel-docente/intervenciones/", intervenciones.intervenciones_docente, name="intervenciones_docente"),
  path("panel-docente/intervenciones/<int:intervencion_id>/cerrar/", intervenciones.cerrar_intervencion_docente, name="cerrar_intervencion_docente"),
  path("intervenciones/mias/", intervenciones.mis_intervenciones, name="mis_intervenciones"),
  path("banco-preguntas/", banco_ops.banco_preguntas, name="banco_preguntas"),
  path("banco-preguntas/<int:pregunta_id>/editar/", banco_ops.editar_pregunta_banco, name="editar_pregunta_banco"),
  path("banco-preguntas/<int:pregunta_id>/enviar/", banco_ops.enviar_pregunta_revision, name="enviar_pregunta_revision"),
  path("banco-preguntas/<int:pregunta_id>/revisar/", banco_ops.revisar_pregunta_banco, name="revisar_pregunta_banco"),
  path("practica-adaptativa/", adaptativo_ops.practica_adaptativa, name="practica_adaptativa"),
  path("panel-docente/actividad/<int:actividad_id>/editar/", docente_ops.editar_actividad_docente, name="editar_actividad_docente"),
  path("panel-docente/estudiante/<int:matricula_id>/", docente_ops.detalle_estudiante_docente, name="detalle_estudiante_docente"),
  path("gestion/usuarios/<int:usuario_id>/editar/", admin_operaciones.editar_usuario, name="admin_editar_usuario"),
  path("gestion/personas/<int:persona_id>/editar/", admin_operaciones.editar_persona, name="admin_editar_persona"),
  path("gestion/estudiantes/<int:estudiante_id>/editar/", admin_operaciones.editar_necesidades_estudiante, name="admin_editar_necesidades_estudiante"),
  path("gestion/catalogos/<str:tipo>/<int:registro_id>/editar/", admin_operaciones.editar_catalogo, name="admin_editar_catalogo"),
  path("gestion/matriculas/", admin_escolar.gestion_matriculas_familias, name="admin_matriculas_familias"),
  path("gestion/matriculas/<int:matricula_id>/editar/", admin_escolar.editar_matricula, name="admin_editar_matricula"),
  path("gestion/vinculos/<int:vinculo_id>/editar/", admin_escolar.editar_vinculo_familiar, name="admin_editar_vinculo"),
  path("gestion/vinculos/<int:vinculo_id>/desvincular/", admin_escolar.desvincular_familiar, name="admin_desvincular_familiar"),
  path("gestion/reportes/", admin_escolar.reportes_academicos_admin, name="admin_reportes_academicos"),
  path('historial-academico/', historial_academico, name='historial_academico'),
  path('simulacros/', simulacros, name='simulacros'),
  path('orientacion-vocacional/', portal_academico.orientacion_vocacional, name='orientacion_vocacional'),
  path('plan-semanal/', portal_academico.plan_estudio, name='plan_semanal'),
  path('diagnostico-academico/', portal_academico.diagnostico_academico, name='diagnostico_academico'),
  path('prediccion-academica/', prediction_views.prediccion_estudiante, name='prediccion_estudiante'),
  path('gestion/validacion-prediccion/', prediction_views.validacion_prediccion, name='validacion_prediccion'),
  path('panel-docente/', portal_academico.panel_docente, name='panel_docente'),
  path('privacidad/', privacy_views.privacidad, name='privacidad'),
  path('privacidad/exportar/', privacy_views.exportar_mis_datos, name='exportar_mis_datos'),
  path('gestion/asignaciones-docentes/', views.gestion_docentes, name='admin_asignaciones_docentes'),
    
  path('',views.home,name="home"), # url home 
  path('testDeVocacion/',views.test,name="test"), # url test
  path('recomendaciones/',views.recomendaciones,name="recomendaciones"), # url recomendaciones
  path('actividadesUsuario/',views.actividadesUsuario,name="actividadesUsuario"), # url recomendaciones
  path('compararCarreras/',portal_academico.comparador_carreras,name="comparadorDeCarreras"), # url comparar carreras
  path('configuraciones/',views.configuraciones,name="configuraciones"), # configuraciones
  path('perfil/',views.perfil,name="perfil"), # url perfil de usuario
  path('registro/',views.registro,name="registro"),
  path('verificar-correo/<str:token>/', views.verificar_correo, name="verificar_correo"), # url registro 
  path('gestion_acudientes_estudiantes/',views.gestion_acudientes_estudiantes,name="gestion_acudientes_estudiantes"), # url gestion acudientes y docentes
  path('admin_gestion_users/',views.gestion_users,name="admin_gestion_users"), # url gestion admin users 
  path('admin_gestion_academica/',views.gestion_academica,name="admin_gestion_academica"), # url gestion academica 
  path('admin_gestion_db/',views.gestion_db,name="admin_gestion_db"), # url gestion academica 
  # path('docentes/',views.docentes,name="docentes"), # url docentes 
  path('acudiente/',portal_academico.panel_acudiente,name="acudiente"), # url acudiente 
  path('salir/', views.salir, name='salir'), # url logout 
  path('eliminar_admin_gestion_db/<tipo>/<id>',views.eliminar_admin_gestion_db,name="eliminar_admin_gestion_db"),
  path('eliminar_admin_gestion_academico/<tipo>/<id>',views.eliminar_gestion_academica,name="eliminar_admin_gestion_academico"),
  path('eliminar_admin_gestion_users/<tipo>/<id>',views.eliminar_gestion_users,name="eliminar_admin_gestion_users"),
  path('eliminar_gestion_acudientes_estudiantes/<tipo>/<id>',views.eliminar_gestion_acudientes_estudiantes,name='eliminar_gestion_acudientes_estudiantes')
]
