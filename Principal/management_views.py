"""Vistas de administración y gestión académica."""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from .services.privacidad import eliminar_archivos_al_confirmar_cuenta
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AcudienteForm, AnioLectivoForm, CursoForm, EstudianteForm, GradoForm,
    MateriaForm, PersonaForm, RelacionAcudienteForm, RolForm, SexoForm,
    UserRegisterForm,
)
from .models import (
    Acudiente, AnioLectivo, AsignacionDocenteCurso, Curso, Estudiante, Grado, Materia, IntentoEvaluacion, PerfilUsuario,
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
def gestion_docentes(request):
    """Solo administradores conceden y revocan acceso a cursos docentes."""
    error = None
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion == "revocar":
            raw = request.POST.get("asignacion_id", "")
            if raw.isdecimal():
                AsignacionDocenteCurso.objects.filter(pk=int(raw)).update(activo=False)
                return redirect("admin_asignaciones_docentes")
            error = "Selecciona una asignación válida."
        elif accion == "asignar":
            raw_usuario = request.POST.get("docente", "")
            raw_curso = request.POST.get("curso", "")
            raw_anio = request.POST.get("anio_lectivo", "")
            if all(c.isdecimal() for c in (raw_usuario, raw_curso, raw_anio)):
                docente = PerfilUsuario.objects.filter(
                    user_id=int(raw_usuario), user__is_active=True,
                    roles__nombre__iexact="DOCENTE"
                ).first()
                curso = Curso.objects.filter(pk=int(raw_curso), activo=True).first()
                anio = AnioLectivo.objects.filter(pk=int(raw_anio)).first()
                if docente and curso and anio:
                    asignacion, creada = AsignacionDocenteCurso.objects.get_or_create(
                        docente=docente, curso=curso, anio_lectivo=anio,
                        defaults={"activo": True},
                    )
                    if not creada and not asignacion.activo:
                        asignacion.activo = True
                        asignacion.save(update_fields=["activo"])
                    return redirect("admin_asignaciones_docentes")
            error = "Selecciona un docente activo, curso activo y año lectivo válidos."
        else:
            error = "Acción no permitida."

    return render(request, "AdminAsignacionesDocentes.html", {
        "error": error,
        "docentes": PerfilUsuario.objects.filter(
            user__is_active=True, roles__nombre__iexact="DOCENTE"
        ).select_related("user").distinct().order_by("user__username"),
        "cursos": Curso.objects.filter(activo=True).select_related("grado").order_by("grado__nombre", "nombre"),
        "anios": AnioLectivo.objects.all().order_by("-anio"),
        "asignaciones": AsignacionDocenteCurso.objects.select_related(
            "docente__user", "curso__grado", "anio_lectivo"
        ).order_by("-activo", "docente__user__username", "-anio_lectivo__anio"),
    })

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

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_users(request):
    users = User.objects.all().order_by('-date_joined', 'pk')
    personas = Persona.objects.all().order_by('nombre')
    form_usuarios = UserRegisterForm()
    form_personas = PersonaForm()
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
            form_personas = PersonaForm(request.POST)
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
