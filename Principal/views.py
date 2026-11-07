"""Fachada de compatibilidad de las URLs y los tests de Pre-ICFES.

Las implementaciones están en Principal.view_modules por responsabilidad.
Conservar estos símbolos permite mantener las rutas y los mocks históricos.
"""
from django.shortcuts import render

from django.conf import settings

if not settings.DEMO_MODE:
    from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
else:
    chatbotManager = None
from Principal.services.gestion_view_test import generar_quizes, generar_material
from Principal.services.verificacion_correo import enviar_verificacion

from .view_modules import autenticacion as _autenticacion
from .view_modules import chatbot as _chatbot
from .view_modules import cuestionarios as _cuestionarios
from .view_modules.autenticacion import inicioDeSesion, salir, verificar_correo
from .view_modules.estudiantes import actividadesUsuario, recomendaciones
from .view_modules.perfiles import configuraciones, editarPerfil, perfil
from .view_modules.vocacional import comparadorDeCarreras

# Mantener los nombres administrativos que consumen Principal/urls.py.
from .management_views import (
    acudiente,
    eliminar_admin_gestion_db,
    eliminar_gestion_academica,
    eliminar_gestion_acudientes_estudiantes,
    eliminar_gestion_users,
    es_gestor,
    gestion_academica,
    gestion_acudientes_estudiantes,
    gestion_db,
    gestion_users,
    gestion_docentes,
)


def home(request):
    """Compatibilidad con pruebas que inyectan Principal.views.render."""
    return _chatbot.home(request, render_func=render)


def test(request):
    """Compatibilidad con pruebas que sustituyen generadores en esta fachada."""
    return _cuestionarios.test(
        request,
        generar_quizes_func=generar_quizes,
        generar_material_func=generar_material,
    )


def registro(request):
    """Compatibilidad con pruebas de envío de verificación por correo."""
    return _autenticacion.registro(
        request, enviar_verificacion_func=enviar_verificacion,
    )
