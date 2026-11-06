"""Perfil del usuario y preferencias de presentación."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from Principal.forms import EstudianteForm, PersonaForm, UserRegisterForm
from Principal.models import Estudiante, EstudianteAcudiente, Matricula, PerfilUsuario, Persona

@login_required
def configuraciones(request):
    return render(request,"Configuraciones.html")     # view Cnfiguraciones
# ********************************CONFIGURACIONES**************************************************



# =============================PERFIL DE USUARIO======================================


@login_required
def perfil(request):
    perfil_usuario = PerfilUsuario.objects.filter(user=request.user).first()
    persona = Persona.objects.filter(perfil_user=perfil_usuario).select_related("sexo").first() if perfil_usuario else None
    estudiante = Estudiante.objects.filter(persona=persona).first() if persona else None
    matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).select_related(
        "curso__grado", "anio_lectivo"
    ).first() if estudiante else None
    vinculos = EstudianteAcudiente.objects.filter(estudiante=estudiante).select_related(
        "acudiente__persona", "relacion"
    ) if estudiante else EstudianteAcudiente.objects.none()
    return render(request, "PerfilDeUsuarios.html", {
        "persona": persona, "estudiante": estudiante,
        "matricula": matricula, "vinculos": vinculos,
        "perfil_usuario": perfil_usuario
    })


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

