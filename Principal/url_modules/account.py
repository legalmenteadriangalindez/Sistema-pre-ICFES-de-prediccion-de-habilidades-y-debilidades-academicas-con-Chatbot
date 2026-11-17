"""Rutas de inicio, autenticación y perfil."""

from django.urls import path

from Principal import portal_academico, views

urlpatterns = [
    path("", views.home, name="home"),
    path("testDeVocacion/", views.test, name="test"),
    path("recomendaciones/", views.recomendaciones, name="recomendaciones"),
    path("actividadesUsuario/", views.actividadesUsuario, name="actividadesUsuario"),
    path(
        "compararCarreras/",
        portal_academico.comparador_carreras,
        name="comparadorDeCarreras",
    ),
    path("configuraciones/", views.configuraciones, name="configuraciones"),
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/editar/", views.editarPerfil, name="perfil_editar"),
    path("registro/", views.registro, name="registro"),
    path(
        "verificar-correo/<str:token>/",
        views.verificar_correo,
        name="verificar_correo",
    ),
    path("acudiente/", portal_academico.panel_acudiente, name="acudiente"),
    path("salir/", views.salir, name="salir"),
]
