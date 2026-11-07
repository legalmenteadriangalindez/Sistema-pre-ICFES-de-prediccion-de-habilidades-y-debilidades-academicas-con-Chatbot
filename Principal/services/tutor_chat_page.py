"""Datos de lectura para la portada del tutor: sin escrituras de perfiles.

El acceso GET solo consulta registros propios, historial y memoria existente.
Las modificaciones de perfil académico pertenecen al servicio de sincronización.
"""

from Principal.models import (
    ActividadAsignada,
    Estudiante,
    IntentoEvaluacion,
    Matricula,
    PerfilUsuario,
    Persona,
)
from Principal.services.gestion_view_test import agrupar_historial_por_turnos


def seleccionar_chat_id(request):
    """Respeta la preferencia de conversación vigente y las URLs anteriores."""
    chat_id = (
        request.POST.get("chat_id")
        or request.GET.get("chat_id")
        or request.session.get("chat_id_actual")
        or "default"
    )
    if request.GET.get("chat_id"):
        request.session["chat_id_actual"] = chat_id
    return chat_id


def estudiante_de_usuario(user):
    """Obtiene exclusivamente el estudiante vinculado a la cuenta autenticada."""
    perfil = PerfilUsuario.objects.filter(user=user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    return Estudiante.objects.filter(persona=persona).first() if persona else None


def estadisticas_inicio(estudiante):
    """Estadísticas reales para las tarjetas de inicio; no modifica registros."""
    intentos = (
        list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("-fecha"))
        if estudiante
        else []
    )
    porcentajes = [intento.porcentaje for intento in intentos]
    matricula = (
        Matricula.objects.filter(estudiante=estudiante, activa=True)
        .order_by("-anio_lectivo__anio")
        .first()
        if estudiante
        else None
    )
    tareas = (
        ActividadAsignada.objects.filter(matricula=matricula)
        .select_related("actividad")
        .order_by("-fecha_asignacion")
        if matricula
        else ActividadAsignada.objects.none()
    )
    return {
        "inicio_intentos": len(intentos),
        "inicio_promedio": round(sum(porcentajes) / len(porcentajes), 1)
        if porcentajes
        else 0,
        "inicio_mejor": max(porcentajes) if porcentajes else 0,
        "inicio_pendientes": tareas.filter(completada=False).count(),
        "inicio_actividades": list(tareas[:5]),
    }


def contexto_portada(chatbot, chat_id, estudiante):
    """Prepara exactamente las claves consumidas por home.html."""
    historial = chatbot.get_conversation_history(chat_id, limit=50)
    contexto = {
        "prompt": "",
        "ruta": None,
        "audio_usuario": None,
        "historial": agrupar_historial_por_turnos(historial),
        "response": None,
        "chat_error": None,
        "chat_id": chat_id,
        "chats": chatbot.memory_manager.get_user_chats(),
        "profile": chatbot.memory_manager.get_cognitive_profile(),
    }
    contexto.update(estadisticas_inicio(estudiante))
    return contexto
