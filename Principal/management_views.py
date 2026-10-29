"""Vistas de administración y gestión académica."""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AcudienteForm, AnioLectivoForm, CursoForm, EstudianteForm, GradoForm,
    MateriaForm, PersonaForm, RelacionAcudienteForm, RolForm, SexoForm,
    UserRegisterForm,
)
from .models import (
    Acudiente, AnioLectivo, Curso, Estudiante, Grado, Materia, PerfilUsuario,
    Persona, RelacionAcudiente, Rol, Sexo,
)

def es_gestor(request_user):
    if not request_user.is_authenticated:
        return False
    if request_user.is_superuser:
        return True
    return PerfilUsuario.objects.filter(
        user=request_user, roles__nombre__iexact="ADMIN"
    ).exists()

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

@login_required # @user_passes_test(es_coordinador)
def acudiente(request):
    
    contexto = {
        "acudientes": None,
        "estudiantes": None
    }
    return render(request, "acudiente.html", contexto)

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
