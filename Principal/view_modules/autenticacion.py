"""Autenticación, registro y confirmación de correo electrónico."""
import logging

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core import signing
from django.db import transaction
from django.shortcuts import redirect, render

from Principal.forms import PersonaForm, RegistroEstudianteForm, UserRegisterForm
from Principal.models import Estudiante, PerfilUsuario, Rol
from Principal.services.verificacion_correo import enviar_verificacion, validar_token

def salir(request):
    logout(request)
    return redirect('/')

# =================================HOME=======================================


def inicioDeSesion(request):
    return render(request,"InicioSesion.html")     # view iniciar secion 
# ********************************INICIO DE SESION**************************************************



# =============================REGISTRO ESTUDIANTE ======================================


def registro(request, *, enviar_verificacion_func=enviar_verificacion):
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
                enviar_verificacion_func(user, request)
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

