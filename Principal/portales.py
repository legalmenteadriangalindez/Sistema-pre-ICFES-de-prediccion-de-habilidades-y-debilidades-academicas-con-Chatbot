"""Portales por rol y gestión de actividades con acceso limitado por curso/familia."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AnioLectivoForm, CursoForm, GradoForm, MateriaForm
from .management_views import es_gestor
from .models import (
    Actividad, ActividadAsignada, AnioLectivo, Curso, DocenteCurso,
    EstudianteAcudiente, Grado, IntentoEvaluacion, Materia, Matricula,
    NivelAprendizaje, PerfilUsuario, Tema,
)
from .services.seguimiento_academico import resumen_de_intentos


def tiene_rol(user, rol):
    return user.is_authenticated and PerfilUsuario.objects.filter(
        user=user, roles__nombre__iexact=rol
    ).exists()


def es_docente(user):
    return tiene_rol(user, 'DOCENTE')


def es_acudiente(user):
    return tiene_rol(user, 'ACUDIENTE')


@login_required
@user_passes_test(es_docente, login_url='/accounts/login/')
@require_http_methods(['GET', 'POST'])
def panel_docente(request):
    cursos = Curso.objects.filter(docentes_asignados__docente=request.user).distinct().order_by('grado__nombre', 'nombre')
    matriculas = Matricula.objects.filter(curso__in=cursos, activa=True).select_related(
        'estudiante__persona', 'curso__grado'
    ).order_by('curso__nombre', 'estudiante__persona__nombre')
    matricula_ids = list(matriculas.values_list('id', flat=True))
    actividades = Actividad.objects.filter(activo=True).select_related('tema__materia').order_by('titulo')
    if request.method == 'POST':
        if request.POST.get('accion') == 'asignar_actividad':
            matricula = Matricula.objects.filter(
                pk=request.POST.get('matricula_id'), pk__in=matricula_ids, activa=True
            ).first() if str(request.POST.get('matricula_id', '')).isdigit() else None
            actividad = actividades.filter(pk=request.POST.get('actividad_id')).first() if str(request.POST.get('actividad_id', '')).isdigit() else None
            if matricula and actividad:
                ActividadAsignada.objects.get_or_create(matricula=matricula, actividad=actividad)
                messages.success(request, 'Actividad asignada al estudiante autorizado.')
            else:
                messages.error(request, 'La matrícula o actividad no corresponde a tus cursos.')
            return redirect('panel_docente')
        if request.POST.get('accion') == 'crear_actividad':
            tema = Tema.objects.filter(pk=request.POST.get('tema_id'), activo=True).first() if str(request.POST.get('tema_id', '')).isdigit() else None
            nivel = NivelAprendizaje.objects.filter(pk=request.POST.get('nivel_id'), activo=True).first() if str(request.POST.get('nivel_id', '')).isdigit() else None
            titulo = request.POST.get('titulo', '').strip()[:100]
            descripcion = request.POST.get('descripcion', '').strip()[:2000]
            if tema and nivel and 5 <= len(titulo) <= 100 and descripcion and cursos.exists():
                Actividad.objects.create(tema=tema, nivel=nivel, titulo=titulo, descripcion=descripcion)
                messages.success(request, 'Actividad creada; ahora puedes asignarla a tus estudiantes.')
            else:
                messages.error(request, 'Completa los datos y comprueba que tienes un curso asignado.')
            return redirect('panel_docente')
        return HttpResponseForbidden('Acción no permitida.')

    estudiantes = []
    for m in matriculas:
        intentos = list(IntentoEvaluacion.objects.filter(estudiante=m.estudiante).order_by('-fecha')[:25])
        resumen = resumen_de_intentos(intentos)
        observados = [s for s in resumen if s['porcentaje'] is not None]
        estudiantes.append({
            'matricula': m, 'total_intentos': len(intentos),
            'areas_prioritarias': [s for s in observados if s['porcentaje'] < 60],
            'tareas_pendientes': ActividadAsignada.objects.filter(matricula=m, completada=False).count(),
            'resumen': observados,
        })
    return render(request, 'panel_docente.html', {
        'cursos': cursos, 'estudiantes': estudiantes, 'matriculas': matriculas,
        'actividades': actividades, 'temas': Tema.objects.filter(activo=True).select_related('materia'),
        'niveles': NivelAprendizaje.objects.filter(activo=True),
        'total_estudiantes': len(estudiantes),
    })


@login_required
@user_passes_test(es_acudiente, login_url='/accounts/login/')
def panel_acudiente(request):
    enlaces = EstudianteAcudiente.objects.filter(
        acudiente__persona__perfil_user__user=request.user
    ).select_related('estudiante__persona', 'relacion')
    estudiantes = []
    for enlace in enlaces:
        estudiante = enlace.estudiante
        matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).select_related('curso__grado').order_by('-anio_lectivo__anio').first()
        intentos = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by('-fecha')[:25])
        resumen = resumen_de_intentos(intentos)
        estudiantes.append({
            'estudiante': estudiante, 'relacion': enlace.relacion,
            'matricula': matricula, 'total_intentos': len(intentos),
            'resumen': [s for s in resumen if s['porcentaje'] is not None],
            'actividades': ActividadAsignada.objects.filter(matricula=matricula).select_related('actividad').order_by('-fecha_asignacion')[:12] if matricula else [],
        })
    return render(request, 'panel_acudiente.html', {'estudiantes': estudiantes})


@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_http_methods(['GET', 'POST'])
def gestion_docentes(request):
    docentes = PerfilUsuario.objects.filter(roles__nombre__iexact='DOCENTE').select_related('user').distinct()
    ids = list(docentes.values_list('user_id', flat=True))
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear_nivel':
            nombre = request.POST.get('nombre', '').strip()[:50]
            if len(nombre) >= 3:
                NivelAprendizaje.objects.get_or_create(nombre=nombre, defaults={'activo': True})
                messages.success(request, 'Nivel de actividad registrado.')
            else:
                messages.error(request, 'Escribe un nombre válido para el nivel.')
            return redirect('gestion_docentes')
        if accion == 'crear_tema':
            materia_id = request.POST.get('materia_id', '')
            nombre = request.POST.get('nombre', '').strip()[:100]
            materia = Materia.objects.filter(pk=materia_id).first() if materia_id.isdigit() else None
            if materia and len(nombre) >= 3:
                Tema.objects.get_or_create(materia=materia, nombre=nombre, defaults={'activo': True})
                messages.success(request, 'Tema académico registrado.')
            else:
                messages.error(request, 'Selecciona una materia y escribe un tema válido.')
            return redirect('gestion_docentes')
        docente_id = request.POST.get('docente_id', '')
        curso_id = request.POST.get('curso_id', '')
        if not docente_id.isdigit() or not curso_id.isdigit() or int(docente_id) not in ids:
            messages.error(request, 'Selecciona un docente y un curso válidos.')
            return redirect('gestion_docentes')
        curso = Curso.objects.filter(pk=int(curso_id)).first()
        if not curso:
            messages.error(request, 'El curso no existe.')
            return redirect('gestion_docentes')
        if request.POST.get('accion') == 'asignar':
            DocenteCurso.objects.get_or_create(docente_id=int(docente_id), curso=curso)
            messages.success(request, 'Curso asignado correctamente.')
        elif request.POST.get('accion') == 'retirar':
            DocenteCurso.objects.filter(docente_id=int(docente_id), curso=curso).delete()
            messages.success(request, 'Asignación retirada.')
        return redirect('gestion_docentes')
    return render(request, 'gestion_docentes.html', {
        'docentes': docentes, 'cursos': Curso.objects.filter(activo=True).select_related('grado'),
        'materias': Materia.objects.filter(activo=True).order_by('nombre'), 'niveles': NivelAprendizaje.objects.filter(activo=True).order_by('nombre'),
        'asignaciones': DocenteCurso.objects.select_related('docente', 'curso__grado').order_by('docente__username'),
    })


CATALOGO = {
    'grados': (Grado, GradoForm), 'cursos': (Curso, CursoForm),
    'materias': (Materia, MateriaForm), 'anios': (AnioLectivo, AnioLectivoForm),
}


@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_http_methods(['GET', 'POST'])
def editar_catalogo(request, tipo, pk):
    if tipo not in CATALOGO:
        return HttpResponseForbidden('Sección no válida.')
    modelo, formulario = CATALOGO[tipo]
    objeto = get_object_or_404(modelo, pk=pk)
    form = formulario(request.POST or None, instance=objeto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Registro actualizado.')
        return redirect('admin_gestion_academica')
    return render(request, 'editar_catalogo.html', {'form': form, 'objeto': objeto, 'tipo': tipo})
