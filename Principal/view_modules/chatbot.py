"""Portada estudiantil y tutor conversacional; sin dependencias de administración."""
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
from Principal.models import (
    ActividadAsignada, Estudiante, IntentoEvaluacion, Matricula, PerfilUsuario, Persona,
)
from Principal.services.audio import procesar_audio
from Principal.services.files import guardar_PDFs, validar_pdf, validar_audio
from Principal.services.gestion_view_test import agrupar_historial_por_turnos
from Principal.services.services_view_home import (
    get_records, set_AnalisisCognitivo, set_EstiloAprendizaje,
    set_PerfilPedagogico, set_RitmoAprendizaje,
)
from Principal.services.tutor_academico import construir_contexto_academico
from .selectores import es_gestor

@login_required
def home(request, *, render_func=render):
    user = request.user
    # El login de Django redirige a / para todos los usuarios. En ese punto,
    # enviamos a los gestores a su panel antes de cargar el tutor estudiantil.
    if es_gestor(user):
        return redirect("admin_gestion_users")
    # Enrutamiento por rol antes de inicializar el chatbot de estudiantes.
    if PerfilUsuario.objects.filter(user=user, roles__nombre__iexact="DOCENTE").exists():
        return redirect("panel_docente")
    if PerfilUsuario.objects.filter(user=user, roles__nombre__iexact="ACUDIENTE").exists():
        return redirect("acudiente")
    persona = getattr(user, "persona", None)
    estudiante = getattr(persona, "estudiante", None) if persona else None
    user_id = str(user.id)
    chat_id = (request.POST.get("chat_id") or request.GET.get("chat_id")
               or request.session.get("chat_id_actual") or "default")
    if request.GET.get("chat_id"):
        request.session["chat_id_actual"] = chat_id
    perfil = PerfilUsuario.objects.filter(user= user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first()
    estudiante = Estudiante.objects.filter(persona= persona).first() if persona else None
    # Las estadísticas provienen de los registros del usuario, nunca del mockup.
    intentos = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("-fecha")) if estudiante else []
    porcentajes = [intento.porcentaje for intento in intentos]
    matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).order_by("-anio_lectivo__anio").first() if estudiante else None
    tareas = ActividadAsignada.objects.filter(matricula=matricula).select_related("actividad").order_by("-fecha_asignacion") if matricula else ActividadAsignada.objects.none()
    inicio_stats = {
        "inicio_intentos": len(intentos),
        "inicio_promedio": round(sum(porcentajes) / len(porcentajes), 1) if porcentajes else 0,
        "inicio_mejor": max(porcentajes) if porcentajes else 0,
        "inicio_pendientes": tareas.filter(completada=False).count(),
        "inicio_actividades": list(tareas[:5]),
    }
    chatbot = chatbotManager.get_chatbot(user_id)
    raw_historial = chatbot.get_conversation_history(chat_id, limit=50)
    chats = chatbot.memory_manager.get_user_chats()
    contexto = {
        "prompt": "",
        "ruta": None,
        "audio_usuario": None,
        "historial":  agrupar_historial_por_turnos(raw_historial),
        "response": None,
        "chat_error": None,
        "chat_id": chat_id,
        "chats" : chats,
        "profile": chatbot.memory_manager.get_cognitive_profile()
    } 
    contexto.update(inicio_stats)
    # Utilizar el perfil del gestor de memoria; no depender de rutas de Windows.
    registro = contexto["profile"]
    if isinstance(registro, list):
        registro = next((item for item in reversed(registro) if isinstance(item, dict) and str(item.get("user_id")) == user_id), None)
    if isinstance(registro, dict) and registro.get("general_level") and estudiante:
        level, area, fuertes, debil, errores = get_records(registro)
        ritmo = set_RitmoAprendizaje("Medio", "Desde JSON")
        estilo = set_EstiloAprendizaje("Visual", "Desde JSON")
        set_PerfilPedagogico(estudiante, ritmo, estilo, level)
        set_AnalisisCognitivo(estudiante, level, fuertes, debil, errores)
    # carrera = Carrera.objects.get(nombre="Ingeniería")
    
    # RecomendacionVocacional.objects.create(
    #     matricula=matricula,
    #     carrera=carrera,
    #     compatibilidad=0.80,
    #     conocimientos_necesarios="Álgebra, lógica",
    #     puntaje_requerido=3.5
    # )
    # temas = Tema.objects.filter(nombre__icontains=area)
    
    # for tema in temas:
    #     materiales = MaterialEstudio.objects.filter(tema=tema)
    #     for material in materiales:
    #         MaterialAsignado.objects.create(
    #             matricula=matricula,
    #             material=material
    #         )


    resultado = {"success": False, "response": None}
    
    if request.method == "POST" and "delete_chat" in request.POST:
        chat_objetivo = request.POST.get("chat_id", "")
        if chatbot.delete_chat(chat_objetivo):
            request.session.pop("chat_id_actual", None)
            return redirect("home")
        contexto["chat_error"] = "No se pudo eliminar la conversación. Vuelve a intentarlo."
        return render_func(request, "home.html", contexto)

    if request.method == "POST":
        # return render_func(request,"home.html",contexto) 
        # ==============datos del contexto============
        prompt= request.POST.get("prompt","").strip()
        pdf = request.FILES.get("archivo")
        audio=request.FILES.get("audio")
        # Validar antes de llamar al LLM y antes de escribir a disco.
        try:
            if pdf:
                validar_pdf(pdf)
            if audio:
                validar_audio(audio)
        except ValidationError as exc:
            contexto["chat_error"] = " ".join(exc.messages)
            return render_func(request, "home.html", contexto)

        
         # ==============borrar historial============
        if "borrarHistorial" in request.POST:
            if chatbot.clear_conversation(chat_id):
                contexto["historial"] = []
            else:
                contexto["chat_error"] = "No se pudo vaciar la conversación."
            return render_func(request,"home.html",contexto)
        # **************borrar historial*************


        #===============crear nuevo chat ===========
        
        # crear un nuevo chat
        if "nuevo_chat" in request.POST:
            chat_id = chatbot.memory_manager.create_new_chat(prompt or "Nuevo Chat")
            contexto["chat_id"] = chat_id
            request.session["chat_id_actual"] = chat_id
            contexto["historial"] = []
        #***************crear nuevo chat************

        # =========enviar mensaje al chatbot========
        if prompt:
            # Contexto construido desde la base de datos del usuario autenticado.
            resumen = construir_contexto_academico(estudiante)
            resultado = chatbot.chat(prompt, chat_id=chat_id, academic_context=resumen)
            # El motor puede crear un UUID cuando se usa el chat inicial "default".
            # Conservar ese identificador para que la siguiente pregunta siga el hilo.
            chat_id = resultado.get("chat_id") or chat_id
            contexto["chat_id"] = chat_id
            request.session["chat_id_actual"] = chat_id
            if resultado["success"]:
                contexto["response"] = resultado["response"]
            else:
                contexto["chat_error"] = f"No pudimos generar una respuesta: {resultado['error']}"
        #***********enviar mensaje al chatbot*******

        # ==actualizar historial después de enviar mensaje==
        contexto["historial"] = agrupar_historial_por_turnos(
           chatbot.get_conversation_history(chat_id, limit=50)
        )
        # **actualizar historial después de enviar mensaje**


        # ==============guardar pdf============
        if pdf:
            try:
                guardar_PDFs(pdf, user_id=request.user.pk)
            except (ValidationError, OSError):
                logging.getLogger(__name__).exception("No se pudo guardar el PDF del usuario %s", request.user.pk)
                contexto["chat_error"] = "No se pudo guardar el PDF. Intenta nuevamente."
        # **************guardar pdf*************
    
        # ==============procesar audio============
        if audio:
            try:
                contexto["audio_usuario"], contexto["ruta"] = procesar_audio(
                    audio, user_id=request.user.pk
                )
            except Exception:
                logging.getLogger(__name__).exception("Error al procesar audio del usuario %s", request.user.pk)
                contexto["chat_error"] = "No se pudo transcribir el audio. Verifica el formato y vuelve a intentarlo."                
        # **************procesar audio*************
            
        contexto["chats"] = chatbot.memory_manager.get_user_chats()
        contexto["prompt"] = prompt

    return render_func(request,"home.html",contexto)       # view home 

# ********************************HOME**************************************************



# ==============================TEST===============================================

