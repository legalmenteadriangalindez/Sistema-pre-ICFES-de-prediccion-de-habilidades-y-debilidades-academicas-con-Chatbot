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
from .models import *

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



#======================================ADMIN GESTION DB=====================================================================
def gestion_db(request):
    roles = Rol.objects.all()
    sexos = Sexo.objects.all()
    Relacion_acudientes = RelacionAcudiente.objects.all()
    if request.method == "POST":
        form_roles = RolForm(request.POST)
        form_sexos = SexoForm(request.POST)
        form_rel = RelacionAcudienteForm(request.POST)
        if form_roles.is_valid():
            form_roles.save()
            redirect('admin_gestion_db')
        if form_sexos.is_valid():
            form_sexos.save()
        if form_rel.is_valid():
            form_rel.save()
    else :
        form_roles= RolForm()
        form_sexos = SexoForm()
        form_rel = RelacionAcudienteForm()
    contexto = {
        "roles": roles,
        "sexos": sexos,
        "Relacion_acudientes": Relacion_acudientes,
        "form_roles": form_roles,
        "form_sexos": form_sexos,
        "form_relaciones": form_rel
    }
    return render(request, "admin_gestion_db.html", contexto)

def eliminar_admin_gestion_db(request,tipo,id):
    if tipo == "rol":
      rol = Rol.objects.get(id=id)
      rol.delete()
    if tipo == "sexo":
        sexo = Sexo.objects.get(id=id)
        sexo.delete()
    if tipo == "relaciones":
        relacion = RelacionAcudiente.objects.get(id=id)
        relacion.delete()
    return redirect('admin_gestion_db')
#***************************************ADMIN GESTION DB********************************************************************




# =======================================GESTION ACUDIENTES Y ESTUDIANTES======================================================================
# @login_required
# @user_passes_test(es_coordinador)
def gestion_acudientes_estudiantes(request):

    estudiantes = Estudiante.objects.all()
    acudientes = Acudiente.objects.all()
    if request.method == "POST":
        tipo_form= request.POST.get("form")
        if tipo_form == "estudiantes":
            form_estudiantes = EstudianteForm(request.POST)
            if form_estudiantes.is_valid():
                form_estudiantes.save()
        else:
            form_estudiantes = EstudianteForm(request.POST)
        if tipo_form == "acudientes":
            if form_acudientes.is_valid():
               form_acudientes.save()
        else:
           form_acudientes = AcudienteForm(request.POST)
    else :
        form_estudiantes = EstudianteForm()
        form_acudientes = AcudienteForm()
    contexto = {
        "estudiantes": estudiantes,
        "acudientes": acudientes,
        "form_estudiantes": form_estudiantes,
        "form_acudientes": form_acudientes
    }
    return render(request, "gestion_estudiantes_acudientes.html", contexto)

def eliminar_gestion_acudientes_estudiantes(request,tipo,id):
    if tipo == "estudiantes":
        estudiante = Estudiante.objects.get(id=id)
        estudiante.delete()
    if tipo == "acudientes":
        acudiente=Acudiente.objects.get(id=id)
        acudiente.delete()
    return redirect('gestion_acudientes_estudiantes')
#************************************GESTION ESTUDIANTES Y ACUDIENTES******************************************************



# =======================================ADMINISTRADOR GESTION USUARIOS======================================================================
# @login_required
# @user_passes_test(es_coordinador)
def gestion_users(request):
    users = User.objects.all()
    personas = Persona.objects.all()
    if request.method == "POST":
        tipo_form = request.POST.get("form")
        if tipo_form == "usuarios":
            form_usuarios = UserRegisterForm(request.POST)
            if form_usuarios.is_valid():
               form_usuarios.save()
        else:
            form_usuarios = UserRegisterForm(request.POST)
        if tipo_form == "personas":
            form_personas = PersonaForm(request.POST)
            if form_personas.is_valid():
               form_personas.save()
        else:
            form_personas = PersonaForm(request.POST)
    else :
        form_personas = PersonaForm()
        form_usuarios = UserRegisterForm()
    contexto = {
        "usuarios": users,
        "personas": personas,
        "form_personas": form_personas,
        "form_usuarios": form_usuarios
    }
    return render(request, "admin_gestion_user.html", contexto)

def eliminar_gestion_users(request,tipo,id):
    if tipo =="usuarios":
        user = User.objects.get(id=id)
        user.delete()
    if tipo == "personas":
        persona = Persona.objects.get(id=id)
        persona.delete()
    return redirect('admin_gestion_user')
#************************************ADMINISTRADOR GESTION USUARIOS******************************************************



# =======================================ACUDIENTE======================================================================
# @login_required
# @user_passes_test(es_coordinador)
@login_required
def acudiente(request):
    
    contexto = {
        "acudientes": None,
        "estudiantes": None
    }
    return render(request, "acudiente.html", contexto)
#************************************ACUDIENTE******************************************************



# =======================================ADMIN GESTION ACADEMICA======================================================================
# @login_required
# @user_passes_test(es_coordinador)
def gestion_academica(request):
    grados = Grado.objects.all()
    Jornadas = Jornada.objects.all()
    cursos = Curso.objects.all()
    sedes = Sede.objects.all()
    anio_lectivos= AnioLectivo.objects.all()
    periodos= PeriodoAcademico.objects.all()
    materias = Materia.objects.all()
    
    if request.method == "POST":
        tipo_form = request.POST.get("form")

        if tipo_form == "grados":
            form_grados = GradoForm(request.POST)
            if form_grados.is_valid():
               form_grados.save()
        else:
            form_grados = GradoForm(request.POST)

        if tipo_form == "cursos":
            form_cursos = CursoForm(request.POST)
            if form_cursos.is_valid():
               form_cursos.save()
        else :
           form_cursos = CursoForm(request.POST) 

        if tipo_form == "jornadas":
           form_jornadas = JornadaForm(request.POST)
           if form_jornadas.is_valid():
               form_jornadas.save()
        else:
            form_jornadas = JornadaForm(request.POST)

        if tipo_form == "sedes":
           form_sedes = SedeForm(request.POST)
           if form_sedes.is_valid():
               form_sedes.save()
        else:
            form_sedes = SedeForm(request.POST)
        
        if tipo_form == "anios":
           form_anio_lectitvo= AnioLectivoForm(request.POST)
           if form_anio_lectitvo.is_valid():
              form_anio_lectitvo.save()
        else:
            form_anio_lectitvo= AnioLectivoForm(request.POST) 
        
        if tipo_form == "periodos":
           form_periodos = PeriodoAcademicoForm(request.POST)
           if form_periodos.is_valid():
               form_periodos.save()
        else:
           form_periodos = PeriodoAcademicoForm(request.POST)  
        
        if tipo_form == "materias":
           form_materias = MateriaForm(request.POST)
           if form_materias.is_valid():
               form_materias.save()
        else:
           form_materias = MateriaForm(request.POST) 
    else :
        form_grados = GradoForm()
        form_cursos = CursoForm()
        form_jornadas = JornadaForm()
        form_sedes = SedeForm()
        form_anio_lectitvo= AnioLectivoForm()
        form_periodos = PeriodoAcademicoForm()
        form_materias = MateriaForm()
    contexto = {
        "cursos": cursos,
        "grados": grados,
        "jornadas": Jornadas,
        "sedes": sedes,
        "anio_lectivo": anio_lectivos,
        "periodos": periodos,
        "materias": materias,
        "form_grados": form_grados,
        "form_cursos": form_cursos,
        "form_jornadas": form_jornadas,
        "form_sedes": form_sedes,
        "form_anios": form_anio_lectitvo,
        "form_periodos": form_periodos,
        "form_materias" : form_materias
    }
    return render(request, "admin_gestion_academica.html", contexto)

def eliminar_gestion_academica(request,tipo,id):
    if tipo == "grados":
        grado = Grado.objects.get(id=id)
        grado.delete()
    if tipo == "jornadas": 
        jornada = Jornada.objects.get(id=id)
        jornada.delete()
    if tipo == "cursos":
        curso = Curso.objects.get(id=id)
        curso.delete()
    if tipo == "sedes":
        sede = Sede.objects.get(id=id)
        sede.delete()
    if tipo == "anios":
        anio_lectivo = AnioLectivo.objects.get(id=id)
        anio_lectivo.delete()
    if tipo == "periodos":
        periodo = PeriodoAcademico.objects.get(id=id)
        periodo.delete()
    if tipo == "materias":
        materia = Materia.objects.get(id=id)
        materia.delete()
    return redirect('admin_gestion_academica')
#************************************ADMINISTRADOR GESTION ACADEMICA******************************************************



# =======================================DOCENTES======================================================================
# @login_required
# @user_passes_test(es_coordinador)

def docentes(request):
    asignacion_docentes = AsignacionDocente.objects.all()
    contexto = {
        "a_docentes": asignacion_docentes
    }
    return render(request, "docentes.html", contexto)
#************************************DOCENTES******************************************************


