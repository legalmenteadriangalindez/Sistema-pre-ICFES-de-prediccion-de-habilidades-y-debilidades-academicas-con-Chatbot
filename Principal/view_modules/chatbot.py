"""Enrutamiento de la portada del tutor, sin lógica de perfil ni adjuntos.

La fachada Principal.views.home sigue utilizando render_func para que los
mocks y las URLs históricas continúen funcionando.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
from Principal.models import PerfilUsuario
from Principal.services.tutor_chat_actions import procesar_post_chat
from Principal.services.tutor_chat_page import (
    contexto_portada,
    estudiante_de_usuario,
    seleccionar_chat_id,
)

from .selectores import es_gestor


@login_required
def home(request, *, render_func=render):
    usuario = request.user
    if es_gestor(usuario):
        return redirect("admin_gestion_users")
    if PerfilUsuario.objects.filter(user=usuario, roles__nombre__iexact="DOCENTE").exists():
        return redirect("panel_docente")
    if PerfilUsuario.objects.filter(user=usuario, roles__nombre__iexact="ACUDIENTE").exists():
        return redirect("acudiente")

    estudiante = estudiante_de_usuario(usuario)
    chat_id = seleccionar_chat_id(request)
    chatbot = chatbotManager.get_chatbot(str(usuario.id))
    contexto = contexto_portada(chatbot, chat_id, estudiante)

    if request.method == "POST":
        return procesar_post_chat(
            request, chatbot, contexto, estudiante, chat_id, render_func
        )
    return render_func(request, "home.html", contexto)
