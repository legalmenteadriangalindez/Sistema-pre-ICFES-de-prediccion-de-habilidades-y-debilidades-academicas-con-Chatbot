"""Acciones POST de la portada: mensajes, hilos y adjuntos del estudiante."""

import logging

from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from Principal.services.audio import procesar_audio
from Principal.services.files import guardar_PDFs, validar_audio, validar_pdf
from Principal.services.documentos_tutor import contexto_de_pdf, extraer_texto_pdf
from Principal.services.gestion_view_test import agrupar_historial_por_turnos
from Principal.services.tutor_academico import construir_contexto_academico
from Principal.services.tutor_profile_sync import sincronizar_perfil_academico
from Principal.services.fuentes_validadas import contexto_con_fuentes
from Principal.services.privacidad_educativa import tutor_autorizado

logger = logging.getLogger(__name__)


def procesar_post_chat(request, chatbot, contexto, estudiante, chat_id, render_func):
    """Mantiene la respuesta y las claves de contexto originales de home.html."""
    if "delete_chat" in request.POST:
        chat_objetivo = request.POST.get("chat_id", "")
        if chatbot.delete_chat(chat_objetivo):
            request.session.pop("chat_id_actual", None)
            return redirect("home")
        contexto["chat_error"] = "No se pudo eliminar la conversación. Vuelve a intentarlo."
        return render_func(request, "home.html", contexto)

    prompt = request.POST.get("prompt", "").strip()
    pdf = request.FILES.get("archivo")
    audio = request.FILES.get("audio")
    if (prompt or pdf or audio) and not tutor_autorizado(estudiante):
        contexto["chat_error"] = (
            "Para utilizar el tutor con IA, incluido el envío de audio o PDF, "
            "un acudiente vinculado debe autorizarlo."
        )
        return render_func(request, "home.html", contexto)
    try:
        if pdf:
            validar_pdf(pdf)
        if audio:
            validar_audio(audio)
    except ValidationError as exc:
        contexto["chat_error"] = " ".join(exc.messages)
        return render_func(request, "home.html", contexto)

    if "borrarHistorial" in request.POST:
        if chatbot.clear_conversation(chat_id):
            contexto["historial"] = []
        else:
            contexto["chat_error"] = "No se pudo vaciar la conversación."
        return render_func(request, "home.html", contexto)

    if "nuevo_chat" in request.POST:
        chat_id = chatbot.memory_manager.create_new_chat(prompt or "Nuevo Chat")
        contexto["chat_id"] = chat_id
        request.session["chat_id_actual"] = chat_id
        contexto["historial"] = []

    texto_documento = ""
    if pdf:
        try:
            # Conservamos la compatibilidad con el repositorio privado existente.
            guardar_PDFs(pdf, user_id=request.user.pk)
            texto_documento = extraer_texto_pdf(pdf)
        except ValidationError as exc:
            contexto["chat_error"] = " ".join(exc.messages)
            return render_func(request, "home.html", contexto)
        except OSError:
            logger.warning("tutor_pdf_save_failed", extra={"component": "files"})
            contexto["chat_error"] = "No se pudo guardar el PDF. Intenta nuevamente."
            return render_func(request, "home.html", contexto)

    texto_audio = ""
    if audio:
        try:
            texto_audio, ruta = procesar_audio(audio, user_id=request.user.pk)
            contexto["audio_usuario"] = texto_audio
            # El archivo se mantiene privado; nunca pasamos su ruta al LLM.
            contexto["ruta"] = ruta
            if not isinstance(texto_audio, str) or not texto_audio.strip():
                raise ValueError("La transcripción está vacía")
        except Exception as exc:
            logger.warning(
                "tutor_audio_processing_failed",
                extra={"component": "audio", "error_type": type(exc).__name__},
            )
            contexto["chat_error"] = (
                "No se pudo transcribir el audio. "
                "Verifica el motor de transcripción y vuelve a intentarlo."
            )
            return render_func(request, "home.html", contexto)

    mensaje = prompt
    if texto_audio:
        mensaje = (
            (prompt + "\\n\\n" if prompt else "")
            + "Pregunta dictada por el estudiante: "
            + texto_audio.strip()[:1800]
        )
    if texto_documento and not mensaje:
        mensaje = (
            "Resume los conceptos importantes del PDF adjunto en español y "
            "propón una actividad para practicar. No inventes contenidos."
        )
    if mensaje:
        resumen = construir_contexto_academico(estudiante)
        fuentes_texto, fuentes = contexto_con_fuentes(estudiante, mensaje)
        if fuentes_texto:
            resumen += "\\n\\n" + fuentes_texto
        if texto_documento:
            resumen += "\\n\\n" + contexto_de_pdf(texto_documento)
            contexto["pdf_analizado"] = True
        contexto["fuentes_validadas"] = fuentes
        resultado = chatbot.chat(
            mensaje[:3000], chat_id=chat_id,
            academic_context=resumen[:5000],
        )
        chat_id = resultado.get("chat_id") or chat_id
        contexto["chat_id"] = chat_id
        request.session["chat_id_actual"] = chat_id
        if resultado["success"]:
            contexto["response"] = resultado["response"]
            try:
                perfiles = chatbot.memory_manager.get_cognitive_profile()
                contexto["profile"] = perfiles
                sincronizar_perfil_academico(
                    estudiante, perfiles, str(request.user.id),
                )
            except Exception as exc:
                logger.warning(
                    "tutor_profile_unavailable",
                    extra={
                        "component": "academic_profile",
                        "error_type": type(exc).__name__,
                    },
                )
        else:
            contexto["chat_error"] = (
                f"No pudimos generar una respuesta: {resultado['error']}"
            )

    contexto["historial"] = agrupar_historial_por_turnos(
        chatbot.get_conversation_history(chat_id, limit=50)
    )

    contexto["chats"] = chatbot.memory_manager.get_user_chats()
    contexto["prompt"] = prompt
    return render_func(request, "home.html", contexto)
