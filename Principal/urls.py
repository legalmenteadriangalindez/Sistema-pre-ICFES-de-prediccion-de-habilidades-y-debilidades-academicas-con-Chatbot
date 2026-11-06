from django.urls import path
from . import portal_academico, privacy_views
from . import views # import de la vista
from .simulacros_views import simulacros
from .historial_views import historial_academico 
from django.urls import path, include  # librerias nesesarias para hacer la referencia desde url.py del proyecto 

urlpatterns = [
  path('historial-academico/', historial_academico, name='historial_academico'),
  path('simulacros/', simulacros, name='simulacros'),
  path('orientacion-vocacional/', portal_academico.orientacion_vocacional, name='orientacion_vocacional'),
  path('plan-semanal/', portal_academico.plan_estudio, name='plan_semanal'),
  path('diagnostico-academico/', portal_academico.diagnostico_academico, name='diagnostico_academico'),
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
