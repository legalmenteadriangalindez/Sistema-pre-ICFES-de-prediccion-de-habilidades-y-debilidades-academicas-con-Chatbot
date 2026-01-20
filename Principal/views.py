# ================================IMPORTACIONES===============================================
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from itertools import chain
from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse #, HttpResponse
from Principal.services.files import guardar_PDFs
from Principal.services.audio import procesar_audio
from Principal.services.gestion_view_test import generar_quizes,generar_material,agrupar_historial_por_turnos
# from Principal.services.rag_service import rag_system
from Principal.services.gestion_historial import obtener_historial,eliminar_historial,guardar_ia,guardar_user,procesar_historial
from Principal.services.gestion_prompts import get_chain_chatbot,extraer_texto_ai
from Principal.IA.processor_PDF import prueba
# from Principal.IA.LangGraph.graph_chatbot.graph import chat,chat_memory_deslizante,chat_memory_vectorial
from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager
from .forms import *

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

    user_id = "user_test"
    chat_id = request.GET.get("chat_id","default")
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
            resultado = chatbot.chat(prompt, chat_id=chat_id)
            if resultado["success"]:
                contexto["response"] = resultado["response"]
            else:
                contexto["response"] = f"Error: {resultado['error']}"
        #***********enviar mensaje al chatbot*******

        # ==actualizar historial después de enviar mensaje==
        contexto["historial"] = chatbot.get_conversation_history(chat_id, limit=50)
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
    # ---------------------usuario de testeo----------------------
    user = request.user
    if not user.is_authenticated:
        from django.contrib.auth.models import User
        user, _ = User.objects.get_or_create(username='testuser')
    # -------------------------------------------------------------

    contexto = {
        "preguntas": [],
        "materiales_recomendados": []
    }    
    if request.method == "POST" and "materia" in request.POST:
        materia = request.POST["materia"]

        #generar las preguntas  inicio del grafo de generacion
        preguntas = generar_quizes(materia,1)
        contexto["preguntas"] = preguntas

        #iniciar generacion de materiales        
        materiales_recomendados = generar_material(preguntas)
        contexto["materiales_recomendados"] = materiales_recomendados
    return render(request,"TestDeVocacion.html", contexto)  
# ********************************TEST***************************************



# =============================RECOMENDACIONES======================================
@login_required
def recomendaciones(request):
    return render(request,"Recomendaciones.html")     # view recomendacion de carreras con IA
# ********************************RECOMENDACIONES**************************************************



# =============================CARRERAS======================================
@login_required
def carreras(request):
    return render(request,"Carreras.html")     # view Carreras Profesionales
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
    docente = None
    acudiente = None
    if persona:
       estudiante = getattr(persona, "estudiante", None) if persona else None
       docente = getattr(persona, "docente", None) if persona else None
       if estudiante:
          acudiente = getattr(estudiante, "acudiente", None) if estudiante else None

    contexto ={
        "user": user,
        "persona": persona,
        "estudiante": estudiante,
        "docente": docente,
        "acudiente": acudiente,
        }
    
    return render(request,"PerfilDeUsuario.html",contexto)     # view Perfil de usuario
    
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
        estudiante_form = EstudianteForm(request.POST)

        if (user_form.is_valid()and persona_form.is_valid()and estudiante_form.is_valid()):
            
            user = user_form.save()
            persona = persona_form.save(commit=False)
            persona.user = user
            persona.save()
            estudiante = estudiante_form.save(commit=False)
            estudiante.persona = persona
            estudiante.save()
            inicioDeSesion(request, user)
            return redirect("login")  
    else:
        user_form = UserRegisterForm()
        persona_form = PersonaForm()
        estudiante_form = EstudianteForm()

    return render(request,"Registro.html",{"user_form": user_form,"persona_form": persona_form,"estudiante_form": estudiante_form,},)  # view Registrarse
# ********************************REGISTRO**************************************************



#===================================GESTION ADMIN============================================================
# @login_required
# @user_passes_test(es_admin)
def gestion_admin(request):
    accion = None
    
    if request.method == "POST":
    
        if "registrar_sexo" in request.POST:
            accion = "sexo"
            sexo_form = SexoForm(request.POST)
            if sexo_form.is_valid():
                sexo_form.save()

        elif "registrar_relaciones" in request.POST:
            accion = "relacion"
            relacion_form = RelacionAcudienteForm(request.POST)
            if relacion_form.is_valid():
                relacion_form.save()

        elif "registrar_grados" in request.POST:
            accion = "grado"
            grado_form = GradoForm(request.POST)
            if grado_form.is_valid():
                grado_form.save()

        elif "registrar_jornadas" in request.POST:
            accion = "jornada"
            jornada_form = JornadaForm(request.POST)
            if jornada_form.is_valid():
                jornada_form.save()

        elif "registrar_sedes" in request.POST:
            accion = "sede"
            sede_form = SedeForm(request.POST)
            if sede_form.is_valid():
                sede_form.save()

        elif "registrar_anio_lectivo" in request.POST:
            accion = "anio"
            anio_form = AnioLectivoForm(request.POST)
            if anio_form.is_valid():
                anio_form.save()

        elif "registrar_periodo" in request.POST:
            accion = "periodo"
            periodo_form = PeriodoAcademicoForm(request.POST)
            if periodo_form.is_valid():
                periodo_form.save()

        elif "registrar_materias" in request.POST:
            accion = "materia"
            materia_form = MateriaForm(request.POST)
            if materia_form.is_valid():
                materia_form.save()

    if request.method == "POST":
        # Instanciamos todos los formularios con POST
        sexo_form = SexoForm(request.POST)
        relacion_form = RelacionAcudienteForm(request.POST)
        grado_form = GradoForm(request.POST)
        jornada_form = JornadaForm(request.POST)
        sede_form = SedeForm(request.POST)
        anio_form = AnioLectivoForm(request.POST)
        periodo_form = PeriodoAcademicoForm(request.POST)
        materia_form = MateriaForm(request.POST)

        # Validamos todos los formularios
        if (sexo_form.is_valid() and relacion_form.is_valid() and grado_form.is_valid() 
            and jornada_form.is_valid() and sede_form.is_valid() 
            and anio_form.is_valid() and periodo_form.is_valid() and materia_form.is_valid()
        ):
            sexo_form.save()
            relacion_form.save()
            grado_form.save()
            jornada_form.save()
            sede_form.save()
            anio_form.save()
            periodo_form.save()
            materia_form.save()

            return redirect("gestion_admin")  # redirigir para limpiar POST
    else:
        # Inicializamos formularios vacíos
        sexo_form = SexoForm()
        relacion_form = RelacionAcudienteForm()
        grado_form = GradoForm()
        jornada_form = JornadaForm()
        sede_form = SedeForm()
        anio_form = AnioLectivoForm()
        periodo_form = PeriodoAcademicoForm()
        materia_form = MateriaForm()

    context = {
        "accion": accion,
        "sexo_form": sexo_form,
        "relacion_form": relacion_form,
        "grado_form": grado_form,
        "jornada_form": jornada_form,
        "sede_form": sede_form,
        "anio_form": anio_form,
        "periodo_form": periodo_form,
        "materia_form": materia_form,
    }

    return render(request, "gestion_admin.html", context)

#***************************************GESTION ADMIN*********************************************************


# =======================================GESTION ACUDIENTES Y ESTUDIANTES======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def gestion_acudientes_estudiantes(request):
    accion = None

    if request.method == "POST" and "registrar_acudiente" in request.POST:
        accion = "acudiente"

        persona_form = PersonaForm(request.POST)

        if persona_form.is_valid():
            
            persona = persona_form.save(commit=False)
            persona.sexo_id = request.POST.get("sexo")
            persona.save()

            
            relacion_id = request.POST.get("relacion")
            acudiente = Acudiente.objects.create(
                persona=persona,
                relacion_id=relacion_id
            )

            
            estudiante_id = request.POST.get("estudiante")
            estudiante = get_object_or_404(Estudiante, id=estudiante_id)

            estudiante.acudiente = acudiente
            estudiante.save()

            return redirect("gestion_acudientes_estudiantes")

    else:
        persona_form = PersonaForm()

    contexto = {
        "accion": accion,
        "persona_form": persona_form,
        "sexos": Sexo.objects.filter(activo=True),
        "relacion_acudientes": RelacionAcudiente.objects.filter(activo=True),
        "estudiantes": Estudiante.objects.filter(acudiente__isnull=True)
                                          .select_related("persona"),
    }
    estudiantes = Estudiante.objects.filter(acudiente__isnull=True).select_related("persona")
    print("Cantidad estudiantes disponibles:", estudiantes.count())
    for e in estudiantes:
        print(e.id, e.persona.nombre, e.persona.apellido)
    return render(request, "gestion_estudiantes_acudientes.html", contexto)

#************************************GESTION ESTUDIANTES Y ACUDIENTES******************************************************



# =======================================ADMINISTRADOR GESTION USUARIOS======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def gestion_users(request):
    contexto = {
        "DATO": "dato"
    }
    return render(request, "admin_gestion_user.html", contexto)

#************************************ADMINISTRADOR GESTION USUARIOS******************************************************


# =======================================ACUDIENTE======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def acudiente(request):
    contexto = {
        "DATO": "dato"
    }
    return render(request, "acudiente.html", contexto)

#************************************ACUDIENTE******************************************************


# =======================================ADMIN GESTION ACADEMICA======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def gestion_academica(request):
    contexto = {
        "DATO": "dato"
    }
    return render(request, "admin_gestion_academica.html", contexto)

#************************************ADMINISTRADOR GESTION ACADEMICA******************************************************


# =======================================DOCENTES======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def docentes(request):
    contexto = {
        "DATO": "dato"
    }
    return render(request, "docentes.html", contexto)

#************************************DOCENTES******************************************************
