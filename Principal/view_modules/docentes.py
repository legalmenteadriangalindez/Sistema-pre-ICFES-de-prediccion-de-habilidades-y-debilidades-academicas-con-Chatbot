"""Acceso docente por curso/año y gestión de actividades con permisos."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from Principal.models import (
    Actividad, ActividadAsignada, AsignacionDocenteCurso, Matricula,
    NivelAprendizaje, Tema,
)
from .selectores import _tiene_rol

def matriculas_permitidas_docente(user):
    """Un docente solo puede acceder a matrículas de sus pares (curso, año).

    Se comparan ambos campos simultáneamente: filtrar cursos y años
    independientemente permitiría ver combinaciones ajenas.
    """
    base = Matricula.objects.filter(activa=True)
    if user.is_superuser:
        return base
    asignaciones = AsignacionDocenteCurso.objects.filter(
        docente__user=user, activo=True, docente__user__is_active=True,
        curso__activo=True,
    ).values_list("curso_id", "anio_lectivo_id")
    permiso = Q(pk__in=[])
    for curso_id, anio_id in asignaciones:
        permiso |= Q(curso_id=curso_id, anio_lectivo_id=anio_id)
    return base.filter(permiso)


@login_required
@require_http_methods(["GET", "POST"])
def panel_docente(request):
    if not _tiene_rol(request.user, "DOCENTE"):
        raise PermissionDenied("Necesitas el rol DOCENTE para acceder a esta vista.")

    permitidas = matriculas_permitidas_docente(request.user)
    tiene_cursos = permitidas.exists()
    error, exito = None, None

    if request.method == "POST":
        if not tiene_cursos:
            raise PermissionDenied("El administrador debe asignarte un curso antes de gestionar actividades.")
        if request.POST.get("accion") == "crear":
            titulo = request.POST.get("titulo", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tema_id = request.POST.get("tema", "")
            nivel_id = request.POST.get("nivel", "")
            tema = Tema.objects.filter(pk=int(tema_id), activo=True).first() if tema_id.isdecimal() else None
            nivel = NivelAprendizaje.objects.filter(pk=int(nivel_id), activo=True).first() if nivel_id.isdecimal() else None
            if not titulo or len(titulo) > 100 or not descripcion or len(descripcion) > 2500 or not tema or not nivel:
                error = "Completa título, descripción, tema y nivel válidos para crear la actividad."
            else:
                Actividad.objects.create(titulo=titulo, descripcion=descripcion, tema=tema, nivel=nivel)
                exito = "Actividad creada en el catálogo. Ahora puedes asignarla."
        elif request.POST.get("accion") in ("", "asignar", None):
            id_matricula = request.POST.get("matricula", "")
            id_actividad = request.POST.get("actividad", "")
            if not id_matricula.isdecimal() or not id_actividad.isdecimal():
                error = "Selecciona una matrícula y una actividad válidas."
            else:
                matricula = permitidas.filter(pk=int(id_matricula)).first()
                if not matricula:
                    raise PermissionDenied("No tienes acceso a la matrícula seleccionada.")
                actividad = Actividad.objects.filter(pk=int(id_actividad), activo=True).first()
                if not actividad:
                    error = "La actividad seleccionada no está disponible."
                else:
                    _, creada = ActividadAsignada.objects.get_or_create(
                        matricula=matricula, actividad=actividad
                    )
                    exito = "Actividad asignada correctamente." if creada else "Esa actividad ya estaba asignada."
        else:
            error = "La acción solicitada no está permitida."

    matriculas = permitidas.select_related(
        "estudiante__persona", "curso__grado", "anio_lectivo"
    ).order_by("curso__grado__nombre", "curso__nombre", "estudiante__persona__apellido")[:200]
    actividades = Actividad.objects.filter(activo=True).select_related(
        "tema", "nivel"
    ).order_by("titulo")[:150]
    recientes = ActividadAsignada.objects.filter(
        matricula__in=permitidas
    ).select_related(
        "matricula__estudiante__persona", "actividad"
    ).order_by("-fecha_asignacion")[:15]

    return render(request, "PanelDocente.html", {
        "matriculas": matriculas, "actividades_catalogo": actividades,
        "recientes": recientes, "error": error, "exito": exito,
        "tiene_cursos": tiene_cursos,
        "temas": Tema.objects.filter(activo=True).select_related("materia").order_by("materia__nombre", "nombre")[:150],
        "niveles": NivelAprendizaje.objects.filter(activo=True).order_by("nombre"),
    })

