"""Enrutamiento de la portada del tutor, sin lógica de perfil ni adjuntos.

La fachada Principal.views.home sigue utilizando render_func para que los
mocks y las URLs históricas continúen funcionando.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

# En Render Free la IA está deshabilitada. Evitar cargar Chroma, torch y
# sentence-transformers al importar las rutas del sitio público.
if not settings.DEMO_MODE:
    from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
else:
    chatbotManager = None
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
    if settings.DEMO_MODE:
        # Mantener la misma interfaz y estadísticas académicas del modo local,
        # sin crear memoria vectorial ni llamar al motor Ollama.
        if request.method != "GET":
            return HttpResponseForbidden("El chat no está disponible en la demo.")
        from Principal.services.tutor_chat_page import estadisticas_inicio

        contexto = {
            "demo_mode": True,
            "chat_id": "demo",
            "historial": [],
            "chats": [],
            "chat_error": None,
            "fuentes_validadas": [],
        }
        contexto.update(estadisticas_inicio(estudiante))
        return render_func(request, "home.html", contexto)
    chat_id = seleccionar_chat_id(request)
    chatbot = chatbotManager.get_chatbot(str(usuario.id))
    contexto = contexto_portada(chatbot, chat_id, estudiante)

    if request.method == "POST":
        return procesar_post_chat(
            request, chatbot, contexto, estudiante, chat_id, render_func
        )
    return render_func(request, "home.html", contexto)
