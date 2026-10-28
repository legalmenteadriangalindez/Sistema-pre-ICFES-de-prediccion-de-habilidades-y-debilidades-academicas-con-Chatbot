# ================================IMPORTACIONES===============================================
from django.contrib.auth import logout,login
import os
from django.conf import settings
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from itertools import chain
from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse #, HttpResponse
from Principal.services.files import guardar_PDFs
from Principal.services.audio import procesar_audio
from Principal.services.gestion_view_test import generar_quizes,generar_material,agrupar_historial_por_turnos
from Principal.services.pruebas_ingles import generar_prueba_ingles
from Principal.services.services_view_home import *
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
    user = request.user
    print(user.id)
    persona = getattr(user, "persona", None)
    estudiante = getattr(persona, "estudiante", None) if persona else None
    
    if not estudiante:
       print("Este usuario no tiene estudiante asociado")
    user_id = str(user.id)
    chat_id = request.POST.get("chat_id") or request.GET.get("chat_id", "default")
    perfil = PerfilUsuario.objects.filter(user= user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first()
    estudiante = Estudiante.objects.filter(persona= persona).first()
    matricula = Matricula.objects.filter(estudiante=estudiante,activa=True).first()
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
    ruta = fr"C:\Users\User\Downloads\ProyectoDeGrado\ProyectoDeGrado\DATABASES\USERS\{user.id}\cognitive_profile.json"
 
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
    else:
        print(f"No se encontró el archivo para el usuario {user.id} creando uno nuevo ")
        perfil = chatbot.memory_manager.build_cognitive_profile(raw_historial,user.id)
        chatbot.memory_manager.save_cognitive_profile(dict(perfil))
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)

    registros_usuario = [r for r in data if int(r["user_id"]) == user.id]

    registro = registros_usuario[-1] if registros_usuario else None
    
    level, area, fuertes, debil, errores = get_records(registro)
    ritmo = set_RitmoAprendizaje("Medio", "Desde JSON")
    estilo = set_EstiloAprendizaje("Visual", "Desde JSON")
    if estudiante:
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
            resultado = chatbot.chat(prompt, chat_id=chat_id)
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
    if request.method == "POST" and request.POST.get("verificar_ingles"):
        pendientes = request.session.pop("prueba_ingles_preguntas", None)
        if not pendientes:
            contexto["error_prueba"] = "La prueba expiró. Genera una nueva prueba de inglés."
        else:
            perfil = PerfilUsuario.objects.filter(user=request.user).first()
            persona = Persona.objects.filter(perfil_user=perfil).first()
            estudiante = Estudiante.objects.filter(persona=persona).first()
            if not estudiante:
                contexto["error_prueba"] = "Debes completar tu registro como estudiante para guardar resultados."
            else:
                from collections import defaultdict
                aciertos = 0
                detalles = []
                competencias = defaultdict(lambda: {"aciertos": 0, "total": 0})
                for pregunta in pendientes:
                    respuesta = request.POST.get(f"respuesta_{pregunta['id']}", "")
                    if respuesta not in ("A", "B", "C"):
                        respuesta = ""
                    correcta = respuesta == pregunta["respuesta_correcta"]
                    aciertos += int(correcta)
                    competencia = pregunta["competencia"]
                    competencias[competencia]["total"] += 1
                    competencias[competencia]["aciertos"] += int(correcta)
                    detalles.append({**pregunta, "respuesta_estudiante": respuesta, "es_correcta": correcta})
                with transaction.atomic():
                    intento = IntentoEvaluacion.objects.create(estudiante=estudiante, materia="Inglés", total_preguntas=len(pendientes), aciertos=aciertos)
                    RespuestaEvaluacion.objects.bulk_create([
                        RespuestaEvaluacion(intento=intento, numero=p["id"], competencia=p["competencia"], enunciado=p["contexto"], pregunta=p["pregunta"], opciones=p["opciones"], respuesta_estudiante=p["respuesta_estudiante"], respuesta_correcta=p["respuesta_correcta"], explicacion=p["explicacion"], es_correcta=p["es_correcta"])
                        for p in detalles
                    ])
                contexto["resultado_ingles"] = {"aciertos": aciertos, "total": len(pendientes), "porcentaje": round(100 * aciertos / len(pendientes)), "intento_id": intento.pk}
                contexto["detalles_ingles"] = detalles
                contexto["competencias_ingles"] = [{"nombre": nombre, "aciertos": dato["aciertos"], "total": dato["total"]} for nombre, dato in competencias.items()]
    elif request.method == "POST" and "materia" in request.POST:
        materia = request.POST["materia"]
        if materia.strip().casefold() in ("ingles", "inglés"):
            preguntas = generar_prueba_ingles()
            request.session["prueba_ingles_preguntas"] = preguntas
            request.session.pop("prueba_ingles_claves", None)
            contexto["preguntas_ingles"] = [{k: v for k, v in pregunta.items() if k not in ("respuesta_correcta", "explicacion")} for pregunta in preguntas]
        else:
            preguntas = generar_quizes(materia, 1)
            contexto["preguntas"] = preguntas
            contexto["materiales_recomendados"] = generar_material(preguntas)
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
        estudiante_form = EstudianteForm(request.POST)

        if (user_form.is_valid()and persona_form.is_valid()and estudiante_form.is_valid()):
            
            with transaction.atomic():
                user = user_form.save()
                perfil = PerfilUsuario.objects.create(user=user)
                rol_estudiante, _ = Rol.objects.get_or_create(nombre="ESTUDIANTE")
                perfil.roles.add(rol_estudiante)
                persona = persona_form.save(commit=False)
                persona.perfil_user = perfil
                persona.save()
                estudiante = estudiante_form.save(commit=False)
                estudiante.persona = persona
                estudiante.save()
            login(request, user)
            return redirect("home")  
    else:
        user_form = UserRegisterForm()
        persona_form = PersonaForm()
        estudiante_form = EstudianteForm()

    return render(request,"Registro.html",{"user_form": user_form,"persona_form": persona_form,"estudiante_form": estudiante_form,},)  # view Registrarse
# ********************************REGISTRO**************************************************



def es_gestor(request_user):
    if not request_user.is_authenticated:
        return False
    if request_user.is_superuser:
        return True
    return PerfilUsuario.objects.filter(
        user=request_user, roles__nombre__iexact="ADMIN"
    ).exists()


#======================================ADMIN GESTION DB=====================================================================
@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_db(request):
    roles = Rol.objects.all()
    sexos = Sexo.objects.all()
    Relacion_acudientes = RelacionAcudiente.objects.all()
    if request.method == "POST":
        tipo_form = request.POST.get("form")
        form_roles = RolForm(request.POST if tipo_form == "roles" else None)
        form_sexos = SexoForm(request.POST if tipo_form == "sexos" else None)
        form_rel = RelacionAcudienteForm(request.POST if tipo_form == "relaciones" else None)
        if tipo_form == "roles" and form_roles.is_valid():
            form_roles.save()
            return redirect("admin_gestion_db")
        if tipo_form == "sexos" and form_sexos.is_valid():
            form_sexos.save()
            return redirect("admin_gestion_db")
        if tipo_form == "relaciones" and form_rel.is_valid():
            form_rel.save()
            return redirect("admin_gestion_db")
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

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
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
@login_required # @user_passes_test(es_coordinador)
@user_passes_test(es_gestor, login_url='/accounts/login/')
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
            form_acudientes = AcudienteForm(request.POST)
            if form_acudientes.is_valid():
               form_acudientes.save()
        else:
           form_acudientes = AcudienteForm()
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

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
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
@login_required # @user_passes_test(es_coordinador)
@user_passes_test(es_gestor, login_url='/accounts/login/')
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

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
def eliminar_gestion_users(request,tipo,id):
    if tipo =="usuarios":
        user = User.objects.get(id=id)
        user.delete()
    if tipo == "personas":
        persona = Persona.objects.get(id=id)
        persona.delete()
    return redirect('admin_gestion_users')
#************************************ADMINISTRADOR GESTION USUARIOS******************************************************



# =======================================ACUDIENTE======================================================================
@login_required # @user_passes_test(es_coordinador)
def acudiente(request):
    
    contexto = {
        "acudientes": None,
        "estudiantes": None
    }
    return render(request, "acudiente.html", contexto)
#************************************ACUDIENTE******************************************************



# =======================================ADMIN GESTION ACADEMICA======================================================================
@login_required # @user_passes_test(es_coordinador)
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_academica(request):
    grados = Grado.objects.all()
    cursos = Curso.objects.all()
    anio_lectivos= AnioLectivo.objects.all()
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
        
        if tipo_form == "anios":
           form_anio_lectitvo= AnioLectivoForm(request.POST)
           if form_anio_lectitvo.is_valid():
              form_anio_lectitvo.save()
        else:
            form_anio_lectitvo= AnioLectivoForm(request.POST) 
        

        if tipo_form == "materias":
           form_materias = MateriaForm(request.POST)
           if form_materias.is_valid():
               form_materias.save()
        else:
           form_materias = MateriaForm(request.POST) 
    else :
        form_grados = GradoForm()
        form_cursos = CursoForm()
        form_anio_lectitvo= AnioLectivoForm()
        form_materias = MateriaForm()
    contexto = {
        "cursos": cursos,
        "grados": grados,
        "anio_lectivo": anio_lectivos,
        "materias": materias,
        "form_grados": form_grados,
        "form_cursos": form_cursos,
        "form_anios": form_anio_lectitvo,
        "form_materias" : form_materias
    }
    return render(request, "admin_gestion_academica.html", contexto)

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
def eliminar_gestion_academica(request,tipo,id):
    if tipo == "grados":
        grado = Grado.objects.get(id=id)
        grado.delete()
    if tipo == "cursos":
        curso = Curso.objects.get(id=id)
        curso.delete()
    if tipo == "anios":
        anio_lectivo = AnioLectivo.objects.get(id=id)
        anio_lectivo.delete()
    if tipo == "materias":
        materia = Materia.objects.get(id=id)
        materia.delete()
    return redirect('admin_gestion_academica')
#************************************ADMINISTRADOR GESTION ACADEMICA******************************************************





