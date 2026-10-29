# ================================IMPORTACIONES===============================================
from django.contrib.auth import logout
from django.core import signing
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from Principal.services.verificacion_correo import enviar_verificacion, validar_token
from django.db import transaction
from django.shortcuts import render, redirect
import logging
import unicodedata
from Principal.services.files import guardar_PDFs
from Principal.services.audio import procesar_audio
from Principal.services.gestion_view_test import generar_quizes,generar_material,agrupar_historial_por_turnos
from Principal.services.pruebas_ingles import generar_prueba_ingles
from Principal.services.services_view_home import (
    get_records,
    set_AnalisisCognitivo,
    set_EstiloAprendizaje,
    set_PerfilPedagogico,
    set_RitmoAprendizaje,
)
from Principal.services.evaluaciones import (
    calificar_y_guardar_evaluacion,
    normalizar_preguntas,
    preguntas_para_estudiante,
)
from Principal.services.tutor_academico import construir_contexto_academico
from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
from .forms import (
    EstudianteForm,
    PersonaForm,
    RegistroEstudianteForm,
    UserRegisterForm,
)
from .models import (
    AnalisisCognitivo,
    Estudiante,
    MaterialAsignado,
    Matricula,
    PerfilPedagogico,
    PerfilUsuario,
    Persona,
    RecomendacionVocacional,
    Rol,
)
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
)

# ********************************IMPORTACIONES**************************************************

# def es_admin(user):
#     return user.groups.filter(name="ADMIN").exists()

# def es_coordinador(user):
#     return user.groups.filter(name="COORDINADOR").exists()
# Create your views here. 
#       
def salir(request):
    logout(request)
    return redirect('/')

# =================================HOME=======================================
@login_required
def home(request):
    user = request.user
    persona = getattr(user, "persona", None)
    estudiante = getattr(persona, "estudiante", None) if persona else None
    user_id = str(user.id)
    chat_id = request.POST.get("chat_id") or request.GET.get("chat_id", "default")
    perfil = PerfilUsuario.objects.filter(user= user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first()
    estudiante = Estudiante.objects.filter(persona= persona).first()
    chatbot = chatbotManager.get_chatbot(user_id)
    raw_historial = chatbot.get_conversation_history(chat_id, limit=50)
    chats = chatbot.memory_manager.get_user_chats()
    contexto = {
        "prompt": "",
        "ruta": None,
        "audio_usuario": None,
        "historial":  agrupar_historial_por_turnos(raw_historial),
        "response": None,
        "chat_id": chat_id,
        "chats" : chats,
        "profile": chatbot.memory_manager.get_cognitive_profile()
    } 
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
       chat_id_to_delete = request.POST.get("chat_id")
       chatbot.memory_manager.delete_chat(chat_id_to_delete)

       if chat_id_to_delete == chat_id:
           return redirect("home")
       
       return redirect(f"{request.path}?chat_id={chat_id}")

    if request.method == "POST":
        # return render(request,"home.html",contexto) 
        # ==============datos del contexto============
        prompt= request.POST.get("prompt","").strip()
        pdf = request.FILES.get("archivo")
        audio=request.FILES.get("audio")

        
         # ==============borrar historial============
        if "borrarHistorial" in request.POST:
            chatbot.clear_conversation(chat_id)
            contexto["historial"] = []
            return render(request,"home.html",contexto)
        # **************borrar historial*************


        #===============crear nuevo chat ===========
        
        # crear un nuevo chat
        if "nuevo_chat" in request.POST:
            chat_id = chatbot.memory_manager.create_new_chat(prompt or "Nuevo Chat")
            contexto["chat_id"] = chat_id
            contexto["historial"] = []
        #***************crear nuevo chat************

        # =========enviar mensaje al chatbot========
        if prompt:
            # Contexto construido desde la base de datos del usuario autenticado.
            resumen = construir_contexto_academico(estudiante)
            resultado = chatbot.chat(prompt, chat_id=chat_id, academic_context=resumen)
            if resultado["success"]:
                contexto["response"] = resultado["response"]
            else:
                contexto["response"] = f"Error: {resultado['error']}"
        #***********enviar mensaje al chatbot*******

        # ==actualizar historial después de enviar mensaje==
        contexto["historial"] = agrupar_historial_por_turnos(
           chatbot.get_conversation_history(chat_id, limit=50)
        )
        # **actualizar historial después de enviar mensaje**


        # ==============guardar pdf============
        if pdf:
           guardar_PDFs(pdf)
        # **************guardar pdf*************
    
        # ==============procesar audio============
        if audio:
           contexto["audio_usuario"],contexto["ruta"]= procesar_audio(audio)                
        # **************procesar audio*************
            
        contexto["prompt"] = prompt

    return render(request,"home.html",contexto)       # view home 

# ********************************HOME**************************************************



# ==============================TEST===============================================
@login_required
def test(request):
    contexto = {"preguntas": [], "materiales_recomendados": []}
    if request.method == "POST" and (
        request.POST.get("verificar_ingles") or request.POST.get("verificar_cuestionario")
    ):
        es_ingles = bool(request.POST.get("verificar_ingles"))
        clave_sesion = "prueba_ingles_preguntas" if es_ingles else "prueba_materia_preguntas"
        pendientes = request.session.pop(clave_sesion, None)
        if not pendientes:
            contexto["error_prueba"] = "La evaluación expiró o ya fue calificada. Genera una nueva prueba."
        else:
            perfil = PerfilUsuario.objects.filter(user=request.user).first()
            persona = Persona.objects.filter(perfil_user=perfil).first()
            estudiante = Estudiante.objects.filter(persona=persona).first()
            if not estudiante:
                contexto["error_prueba"] = "Debes completar tu registro como estudiante para guardar resultados."
            else:
                materia = "Inglés" if es_ingles else str(pendientes[0].get("materia", "Evaluación"))
                resultado, detalles, competencias = calificar_y_guardar_evaluacion(
                    estudiante=estudiante,
                    materia=materia,
                    preguntas=pendientes,
                    datos_respuesta=request.POST,
                )
                contexto["materia_evaluacion"] = materia
                contexto["resultado_evaluacion"] = resultado
                contexto["detalles_evaluacion"] = detalles
                contexto["competencias_evaluacion"] = competencias
                if es_ingles:
                    # Mantener las claves de contexto ya utilizadas por el historial de inglés.
                    contexto["resultado_ingles"] = resultado
                    contexto["detalles_ingles"] = detalles
                    contexto["competencias_ingles"] = competencias
    elif request.method == "POST" and "materia" in request.POST:
        entrada = request.POST.get("materia", "").strip()
        clave_materia = "".join(
            caracter
            for caracter in unicodedata.normalize("NFKD", entrada.casefold())
            if not unicodedata.combining(caracter)
        )
        materias = {
            "lectura critica": "Lectura Crítica",
            "matematicas": "Matemáticas",
            "sociales y ciudadanas": "Sociales y Ciudadanas",
            "ciencias naturales": "Ciencias Naturales",
            "ingles": "Inglés",
        }
        materia = materias.get(clave_materia)
        if not materia:
            contexto["error_prueba"] = "Selecciona una materia válida para iniciar la evaluación."
        elif clave_materia == "ingles":
            preguntas = generar_prueba_ingles()
            request.session["prueba_ingles_preguntas"] = preguntas
            contexto["preguntas_ingles"] = preguntas_para_estudiante(preguntas)
        else:
            try:
                preguntas = normalizar_preguntas(generar_quizes(materia, 1), materia)
            except ValueError as error:
                contexto["error_prueba"] = str(error)
            except Exception:
                logging.getLogger(__name__).exception("Falló la generación de un cuestionario")
                contexto["error_prueba"] = (
                    "No fue posible generar el cuestionario en este momento. Intenta nuevamente."
                )
            else:
                # La clave se conserva en la sesión de Django, nunca en el HTML.
                request.session["prueba_materia_preguntas"] = [
                    {**pregunta, "materia": materia} for pregunta in preguntas
                ]
                contexto["preguntas"] = preguntas_para_estudiante(preguntas)
                try:
                    contexto["materiales_recomendados"] = generar_material(preguntas)
                except Exception:
                    logging.getLogger(__name__).exception(
                        "No fue posible generar materiales recomendados para la prueba"
                    )
    return render(request, "TestDeVocacion.html", contexto)
# ********************************TEST***************************************



# =============================RECOMENDACIONES======================================
@login_required
def recomendaciones(request):
    user = request.user

    perfil = PerfilUsuario.objects.filter(user= user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first()
    estudiante = Estudiante.objects.filter(persona= persona).first()

    if not estudiante:
        return render(request,"Recomendaciones.html",{"error": "este perfil no tiene estudiante asociado"})
    
    print(estudiante)
    matricula = Matricula.objects.filter(estudiante=estudiante,activa=True).first()
    perfil_pedagogico = None
    analisis_cognitivo = None
    recomendacion_vocacional = None
    material_estudio_recomendado = None

    perfil_pedagogico = PerfilPedagogico.objects.filter(estudiante=estudiante).first()
    analisis_cognitivo = AnalisisCognitivo.objects.filter(estudiante=estudiante).first()

    recomendacion_vocacional = RecomendacionVocacional.objects.filter(matricula=matricula)
    material_estudio_recomendado = MaterialAsignado.objects.filter(matricula=matricula)


    contexto = {
        "perfil_pedagogico": perfil_pedagogico,
        "analisis_cognitivo": analisis_cognitivo,
        "recomendacion_vocacional": recomendacion_vocacional,
        "material_estudio_recomendado": material_estudio_recomendado,
    }

    return render(request,"Recomendaciones.html",contexto)     # view recomendacion de carreras con IA
#********************************RECOMENDACIONES**************************************************



# =============================CARRERAS======================================
@login_required
def actividadesUsuario(request):
    return render(request,"actividadesUsuario.html")     # view Carreras Profesionales
# # ********************************CARRERAS**************************************************




# =============================COMPARADOR DE CARRERAS======================================
@login_required
def comparadorDeCarreras(request):
    return render(request,"ComparadorDeCarreras.html")     # view Comparador de carreras 
# ********************************COPARADOR DE CARRERAS**************************************************




# =============================CONFIGURACIONES======================================
@login_required
def configuraciones(request):
    return render(request,"Configuraciones.html")     # view Cnfiguraciones
# ********************************CONFIGURACIONES**************************************************



# =============================PERFIL DE USUARIO======================================
@login_required
def perfil(request):
    
    user = request.user
    persona = getattr(user, "persona", None)
    estudiante = None
    # docente = None
    acudiente = None
    if persona:
       estudiante = getattr(persona, "estudiante", None) if persona else None
    #    docente = getattr(persona, "docente", None) if persona else None
       if estudiante:
          acudiente = getattr(estudiante, "acudiente", None) if estudiante else None

    contexto ={
        "user": user,
        "persona": persona,
        "estudiante": estudiante,
        # "docente": docente,
        "acudiente": acudiente,
        }
    
    return render(request,"PerfilDeUsuarios.html",contexto)     # view Perfil de usuario
    
# ********************************PERFIL DE USUARIO**************************************************

@login_required
def editarPerfil(request):
    
    user = request.user
    try: 
        persona = user.persona
    except Exception as e:
        persona = None 

    try: 
        estudiante = persona.estudiante
    except Exception as e:
        estudiante = None 
    
    try: 
        acudiente = estudiante.acudiente
    except Exception as e:
        acudiente = None
    
    try: 
        docente = persona.docente
    except Exception as e :
        docente = None

    
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST,instance= user)
        persona_form = PersonaForm(request.POST, instance=persona)
        estudiante_form = EstudianteForm(request.POST,instance=estudiante) if estudiante else None
        
        forms_validos = user_form.is_valid() and persona_form.is_valid()
        if estudiante_form:
            forms_validos = forms_validos and estudiante_form.is_valid()
        
        if forms_validos: 
            user_form.save()
            persona_form.save()
            if estudiante_form:
                estudiante_form.save()
            return redirect('perfil')
    else:
        user_form= UserRegisterForm(instance=user) 
        persona_form = PersonaForm(instance=persona)
        estudiante_form = EstudianteForm(instance=estudiante) if estudiante else None
    contexto ={
        "user_form": user_form,
        "persona_form": persona_form,
        "estudiante_form": estudiante_form,
        "estudiante": estudiante,
        "acudiente": acudiente,
        "docente": docente
        }
    return render(request,"PerfilDeUsuario.html",contexto)     # view Perfil de usuario

#=====================================EDITAR PERFIL==============================================================


#*************************************EDITAR PERFIL****************************************************************


# =============================INICIO DE SESION======================================

def inicioDeSesion(request):
    return render(request,"InicioSesion.html")     # view iniciar secion 
# ********************************INICIO DE SESION**************************************************



# =============================REGISTRO ESTUDIANTE ======================================
def registro(request):
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        persona_form = PersonaForm(request.POST)
        estudiante_form = RegistroEstudianteForm(request.POST)

        if (user_form.is_valid()and persona_form.is_valid()and estudiante_form.is_valid()):
            
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.is_active = False
                user.save()
                perfil = PerfilUsuario.objects.create(user=user)
                rol_estudiante, _ = Rol.objects.get_or_create(nombre="ESTUDIANTE")
                perfil.roles.add(rol_estudiante)
                persona = persona_form.save(commit=False)
                persona.perfil_user = perfil
                persona.save()
                estudiante = estudiante_form.save(commit=False)
                estudiante.persona = persona
                estudiante.save()
            try:
                enviar_verificacion(user, request)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Error al enviar verificación a través de Brevo")
                return render(request, "verificacion_correo.html", {"estado": "error_envio"})
            return render(request, "verificacion_correo.html", {"estado": "enviado"})  
    else:
        user_form = UserRegisterForm()
        persona_form = PersonaForm()
        estudiante_form = RegistroEstudianteForm()

    return render(request,"Registro.html",{"user_form": user_form,"persona_form": persona_form,"estudiante_form": estudiante_form,},)  # view Registrarse
# ********************************REGISTRO**************************************************



def verificar_correo(request, token):
    try:
        datos = validar_token(token)
    except (signing.BadSignature, signing.SignatureExpired):
        return render(request, "verificacion_correo.html", {"estado": "invalido"}, status=400)
    usuario = User.objects.filter(pk=datos.get("uid"), email__iexact=datos.get("email", "")).first()
    if usuario is None:
        return render(request, "verificacion_correo.html", {"estado": "invalido"}, status=400)
    if usuario.is_active:
        return render(request, "verificacion_correo.html", {"estado": "verificado"})
    usuario.is_active = True
    usuario.save(update_fields=["is_active"])
    return render(request, "verificacion_correo.html", {"estado": "verificado"})


# Las vistas administrativas se reexportan desde Principal.management_views.
