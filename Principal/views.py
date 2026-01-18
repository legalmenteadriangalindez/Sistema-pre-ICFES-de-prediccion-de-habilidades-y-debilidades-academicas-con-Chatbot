# ================================IMPORTACIONES===============================================
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from itertools import chain
from django.shortcuts import render,redirect
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
    return render(request,"PerfilDeUsuario.html")     # view Perfil de usuario
# ********************************PERFIL DE USUARIO**************************************************



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


#=======================================CORDINADOR======================================================================
# @login_required
# @user_passes_test(es_coordinador)
def cordinador(request):
    # Formulario para crear persona
    if request.method == "POST":
        persona_form = PersonaForm(request.POST)
        acudiente_form = AcudienteForm(request.POST)  # relacion con acudiente
        # Otras opciones seleccionadas
        grado_id = request.POST.get("grado")
        jornada_id = request.POST.get("jornada")
        sede_id = request.POST.get("sede")
        materia_id = request.POST.get("materia")
        periodo_id = request.POST.get("periodo")
        anio_id = request.POST.get("anio")

        if persona_form.is_valid() and acudiente_form.is_valid():
            persona = persona_form.save(commit=False)
            persona.user = request.user
            persona.save()

            acudiente = acudiente_form.save(commit=False)
            acudiente.persona = persona
            acudiente.save()

            # Aquí podrías manejar los selects elegidos si los quieres usar
            # ejemplo: grado = Grado.objects.get(id=grado_id)

            return redirect("cordinador")
    else:
        persona_form = PersonaForm()
        acudiente_form = AcudienteForm()

    # Formularios solo como selects
    grados = Grado.objects.filter(activo=True)
    jornadas = Jornada.objects.filter(activo=True)
    sedes = Sede.objects.filter(activo=True)
    materias = Materia.objects.filter(activo=True)
    periodos = PeriodoAcademico.objects.filter(activo=True)
    anios = AnioLectivo.objects.filter(activo=True)
    relacion_acudientes = RelacionAcudiente.objects.filter(activo=True)
    sexos = Sexo.objects.filter(activo=True)

    contexto = {
        "persona_form": persona_form,
        "acudiente_form": acudiente_form,
        "grados": grados,
        "jornadas": jornadas,
        "sedes": sedes,
        "materias": materias,
        "periodos": periodos,
        "anios": anios,
        "relacion_acudientes": relacion_acudientes,
        "sexos": sexos,
    }

    return render(request, "cordinador.html", contexto)

#************************************CORDINADOR******************************************************