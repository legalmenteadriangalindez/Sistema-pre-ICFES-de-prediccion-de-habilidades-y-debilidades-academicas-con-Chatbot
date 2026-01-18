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
  path('cordinador/',views.cordinador,name="cordinador"), # url cordinador 
  path('salir/', views.salir, name='salir') # url logout 
]
