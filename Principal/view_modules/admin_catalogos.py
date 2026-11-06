"""CRUD administrativo de catálogos generales y académicos."""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from Principal.forms import (
    AnioLectivoForm, CursoForm, GradoForm, MateriaForm,
    RelacionAcudienteForm, RolForm, SexoForm,
)
from Principal.models import (
    AnioLectivo, Curso, Grado, Materia, RelacionAcudiente, Rol, Sexo,
)
from .selectores import es_gestor

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

