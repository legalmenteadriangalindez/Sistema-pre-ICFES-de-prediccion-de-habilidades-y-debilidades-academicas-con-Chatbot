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
  path('iniciarSesion/',views.inicioDeSesion,name="inicioDeSesion"), # url inicio de sesion 
  path('registro/',views.registro,name="registro"), # url registro 

]
