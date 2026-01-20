from django.urls import path
from . import views # import de la vista 
from django.urls import path, include  # librerias nesesarias para hacer la referencia desde url.py del proyecto 

urlpatterns = [
    
  path('',views.home,name="home"), # url home 
  path('testDeVocacion/',views.test,name="test"), # url test
  path('recomendaciones/',views.recomendaciones,name="recomendaciones"), # url recomendaciones
  path('carreras/',views.carreras,name="carreras"), # url recomendaciones
  path('compararCarreras/',views.comparadorDeCarreras,name="comparadorDeCarreras"), # url comparar carreras
  path('configuraciones/',views.configuraciones,name="configuraciones"), # configuraciones
  path('perfil/',views.perfil,name="perfil"), # url perfil de usuario
  path('registro/',views.registro,name="registro"), # url registro 
  path('gestion_admin/',views.gestion_admin,name="gestion_admin"), # url gestion admin 
  path('gestion_acudientes_estudiantes/',views.gestion_acudientes_estudiantes,name="gestion_acudientes_estudiantes"), # url gestion acudientes y docentes
  path('admin_gestion_users/',views.gestion_users,name="admin_gestion_users"), # url gestion admin users 
  path('admin_gestion_academica/',views.gestion_academica,name="admin_gestion_academica"), # url gestion academica 
  path('admin_gestion_db/',views.gestion_db,name="admin_gestion_db"), # url gestion academica 
  path('docentes/',views.docentes,name="docentes"), # url docentes 
  path('acudiente/',views.acudiente,name="acudiente"), # url acudiente 
  path('salir/', views.salir, name='salir') # url logout 
]
