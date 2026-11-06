"""Gestión segura de matrículas y vínculos familiares por administración."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .management_views import es_gestor
from .models import (
    Acudiente, AnioLectivo, Curso, Estudiante, EstudianteAcudiente,
    Matricula, RelacionAcudiente,
)


@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_http_methods(['GET','POST'])
def gestion_matriculas_familias(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'matricular':
            estudiante_id = str(request.POST.get('estudiante_id', ''))
            curso_id = str(request.POST.get('curso_id', ''))
            anio_id = str(request.POST.get('anio_id', ''))
            estudiante = Estudiante.objects.filter(pk=int(estudiante_id)).first() if estudiante_id.isdigit() else None
            curso = Curso.objects.filter(pk=int(curso_id), activo=True).first() if curso_id.isdigit() else None
            anio = AnioLectivo.objects.filter(pk=int(anio_id)).first() if anio_id.isdigit() else None
            if estudiante and curso and anio:
                with transaction.atomic():
                    matricula, creada = Matricula.objects.get_or_create(
                        estudiante=estudiante, anio_lectivo=anio,
                        defaults={'curso': curso, 'activa': True},
                    )
                    if not creada and (matricula.curso_id != curso.id or not matricula.activa):
                        matricula.curso, matricula.activa = curso, True
                        matricula.save(update_fields=['curso', 'activa'])
                messages.success(request, 'Matrícula registrada o actualizada correctamente.')
            else:
                messages.error(request, 'Selecciona estudiante, curso activo y año lectivo válidos.')
            return redirect('gestion_matriculas_familias')
        if accion == 'vincular':
            estudiante_id = str(request.POST.get('estudiante_id', ''))
            acudiente_id = str(request.POST.get('acudiente_id', ''))
            relacion_id = str(request.POST.get('relacion_id', ''))
            estudiante = Estudiante.objects.filter(pk=int(estudiante_id)).first() if estudiante_id.isdigit() else None
            acudiente = Acudiente.objects.filter(pk=int(acudiente_id)).first() if acudiente_id.isdigit() else None
            relacion = RelacionAcudiente.objects.filter(pk=int(relacion_id)).first() if relacion_id.isdigit() else None
            if estudiante and acudiente and relacion:
                EstudianteAcudiente.objects.update_or_create(
                    estudiante=estudiante, acudiente=acudiente,
                    defaults={'relacion': relacion},
                )
                messages.success(request, 'Vínculo de acudiente guardado.')
            else:
                messages.error(request, 'Selecciona un vínculo válido.')
            return redirect('gestion_matriculas_familias')
        if accion == 'retirar_vinculo':
            vínculo_id = str(request.POST.get('vinculo_id', ''))
            if vínculo_id.isdigit():
                EstudianteAcudiente.objects.filter(pk=int(vínculo_id)).delete()
                messages.success(request, 'Vínculo retirado.')
            return redirect('gestion_matriculas_familias')
        if accion == 'desactivar_matricula':
            matricula_id = str(request.POST.get('matricula_id', ''))
            if matricula_id.isdigit():
                Matricula.objects.filter(pk=int(matricula_id)).update(activa=False)
                messages.success(request, 'Matrícula desactivada sin eliminar su historial.')
            return redirect('gestion_matriculas_familias')
        messages.error(request, 'Operación no reconocida.')
        return redirect('gestion_matriculas_familias')

    return render(request, 'gestion_matriculas_familias.html', {
        'estudiantes': Estudiante.objects.select_related('persona').order_by('persona__nombre'),
        'cursos': Curso.objects.filter(activo=True).select_related('grado').order_by('grado__nombre','nombre'),
        'anios': AnioLectivo.objects.all().order_by('-anio'),
        'acudientes': Acudiente.objects.select_related('persona').order_by('persona__nombre'),
        'relaciones': RelacionAcudiente.objects.filter(activo=True),
        'matriculas': Matricula.objects.select_related('estudiante__persona','curso','anio_lectivo').order_by('-anio_lectivo__anio')[:100],
        'vinculos': EstudianteAcudiente.objects.select_related('estudiante__persona','acudiente__persona','relacion').order_by('estudiante__persona__nombre')[:100],
    })
