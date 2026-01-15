# ================================IMPORTACIONES===============================================
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
from Principal.IA.LangGraph.graph_chatbot.graph import chat,chat_memory_deslizante,chat_memory_vectorial
from Principal.IA.LangGraph.graph_chatbot.chatbot import chatbotManager

from django.contrib.auth.decorators import login_required
# ********************************IMPORTACIONES**************************************************

# Create your views here.       

# =================================HOME=======================================
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
        "chats" : chats
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

# @login_required(login_url='/iniciarSesion/')
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
def recomendaciones(request):
    return render(request,"Recomendaciones.html")     # view recomendacion de carreras con IA
# ********************************RECOMENDACIONES**************************************************



# =============================CARRERAS======================================
def carreras(request):
    return render(request,"Carreras.html")     # view Carreras Profesionales
# # ********************************CARRERAS**************************************************




# =============================COMPARADOR DE CARRERAS======================================
def comparadorDeCarreras(request):
    return render(request,"ComparadorDeCarreras.html")     # view Comparador de carreras 
# ********************************COPARADOR DE CARRERAS**************************************************




# =============================CONFIGURACIONES======================================
def configuraciones(request):
    return render(request,"Configuraciones.html")     # view Cnfiguraciones
# ********************************CONFIGURACIONES**************************************************



# =============================PERFIL DE USUARIO======================================
def perfil(request):
    return render(request,"PerfilDeUsuario.html")     # view Perfil de usuario
# ********************************PERFIL DE USUARIO**************************************************



# =============================INICIO DE SESION======================================
def inicioDeSesion(request):
    return render(request,"InicioSesion.html")     # view iniciar secion 
# ********************************INICIO DE SESION**************************************************



# =============================REGISTRO ======================================
def registro(request):
    return render(request,"Registro.html")     # view Registrarse
# ********************************REGISTRO**************************************************

