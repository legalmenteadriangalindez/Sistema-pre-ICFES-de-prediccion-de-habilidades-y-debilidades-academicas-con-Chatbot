"""Administración de cuentas y personas; borrado transaccional privado."""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from Principal.forms import UserRegisterForm
from .admin_operaciones import CrearPersonaAdminForm
from Principal.models import (
    Curso, Estudiante, IntentoEvaluacion, PerfilUsuario, Persona, Rol,
)
from Principal.services.privacidad import eliminar_archivos_al_confirmar_cuenta
from .selectores import es_gestor

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_users(request):
    users = User.objects.all().order_by('-date_joined', 'pk')
    personas = Persona.objects.all().order_by('nombre')
    form_usuarios = UserRegisterForm()
    form_personas = CrearPersonaAdminForm()
    error_admin = None
    if request.method == 'POST':
        tipo_form = request.POST.get('form', '')
        if tipo_form == 'usuarios':
            form_usuarios = UserRegisterForm(request.POST)
            if form_usuarios.is_valid():
                nuevo = form_usuarios.save()
                perfil, _ = PerfilUsuario.objects.get_or_create(user=nuevo)
                rol_id = request.POST.get('rol_id', '')
                if rol_id.isdigit():
                    rol = Rol.objects.filter(pk=int(rol_id)).first()
                    if rol:
                        perfil.roles.add(rol)
                return redirect('admin_gestion_users')
        elif tipo_form == 'personas':
            form_personas = CrearPersonaAdminForm(request.POST)
            if form_personas.is_valid():
                form_personas.save()
                return redirect('admin_gestion_users')
        elif tipo_form == 'asignar_rol':
            usuario_id, rol_id = request.POST.get('usuario_id', ''), request.POST.get('rol_id', '')
            if usuario_id.isdigit() and rol_id.isdigit():
                cuenta = User.objects.filter(pk=int(usuario_id)).first()
                rol = Rol.objects.filter(pk=int(rol_id)).first()
                if cuenta and rol:
                    perfil, _ = PerfilUsuario.objects.get_or_create(user=cuenta)
                    perfil.roles.set([rol])
                    return redirect('admin_gestion_users')
            error_admin = 'Selecciona un usuario y un rol válidos.'
        elif tipo_form == 'cambiar_estado':
            usuario_id = request.POST.get('usuario_id', '')
            if usuario_id.isdigit():
                cuenta = User.objects.filter(pk=int(usuario_id)).first()
                if cuenta and cuenta.pk != request.user.pk:
                    cuenta.is_active = not cuenta.is_active
                    cuenta.save(update_fields=['is_active'])
                    return redirect('admin_gestion_users')
            error_admin = 'No puedes modificar el estado de tu propia cuenta.'
    contexto = {
        'usuarios': users,
        'personas': personas,
        'form_personas': form_personas,
        'form_usuarios': form_usuarios,
        'roles': Rol.objects.all().order_by('nombre'),
        'total_usuarios': users.count(),
        'total_estudiantes': Estudiante.objects.count(),
        'total_cursos': Curso.objects.count(),
        'total_evaluaciones': IntentoEvaluacion.objects.count(),
        'error_admin': error_admin,
    }
    return render(request, 'admin_gestion_user.html', contexto)


@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
def eliminar_gestion_users(request,tipo,id):
    """Borrado administrativo coherente: cuenta y datos dependientes.

    Antes se podía borrar solo Persona y dejar una cuenta huérfana.
    La limpieza de carpetas privadas ocurre al confirmarse el commit.
    """
    cuenta = None
    if tipo == "usuarios":
        cuenta = User.objects.filter(pk=id).first()
    elif tipo == "personas":
        persona = Persona.objects.filter(pk=id).select_related(
            "perfil_user__user"
        ).first()
        cuenta = persona.perfil_user.user if persona else None

    if cuenta and cuenta.pk != request.user.pk:
        identificador = cuenta.pk
        with transaction.atomic():
            cuenta.delete()
            eliminar_archivos_al_confirmar_cuenta(identificador)
    return redirect("admin_gestion_users")

