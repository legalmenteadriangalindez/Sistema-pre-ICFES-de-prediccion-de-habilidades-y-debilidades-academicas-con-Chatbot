"""Portales por rol, orientación y seguimiento con los modelos actuales.

No requiere migraciones adicionales ni servicios de IA. Los resultados de
orientación son orientativos y no sustituyen asesoría profesional.
"""
from decimal import Decimal
from datetime import date, timedelta

from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import (
    Actividad, ActividadAsignada, AsignacionDocenteCurso, Carrera, Estudiante, EstudianteAcudiente,
    IntentoEvaluacion, Matricula, NivelAprendizaje, PerfilUsuario, Persona, RecomendacionVocacional, Tema,
    PlanEstudioSemanal, SesionPlanSemanal,
)
from .services.orientacion import AREAS, PREGUNTAS, calcular_perfil
from .services.seguimiento import plan_semanal, resumen_estudiante
from .services.plan_persistente import (
    crear_plan_actual, historial_semanal, lunes_de, marcar_sesion,
    reabrir_sesion, resumen_plan,
)


def _tiene_rol(user, nombre):
    return user.is_authenticated and (user.is_superuser or PerfilUsuario.objects.filter(
        user=user, roles__nombre__iexact=nombre
    ).exists())


def _estudiante(user):
    perfil = PerfilUsuario.objects.filter(user=user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    return Estudiante.objects.filter(persona=persona).first() if persona else None


def _matricula(estudiante):
    return Matricula.objects.filter(estudiante=estudiante, activa=True).first() if estudiante else None


@login_required
@require_http_methods(["GET", "POST"])
def orientacion_vocacional(request):
    estudiante = _estudiante(request.user)
    if not estudiante:
        raise PermissionDenied("Esta orientación requiere un perfil estudiantil.")
    matricula = _matricula(estudiante)
    resultado = request.session.get("orientacion_estudiante_%s" % estudiante.pk)
    error = None
    if request.method == "POST":
        try:
            respuestas = {codigo: request.POST[codigo] for codigo, _, _ in PREGUNTAS}
            areas, carreras = calcular_perfil(respuestas)
        except (KeyError, ValueError) as exc:
            error = str(exc) if isinstance(exc, ValueError) else "Responde todas las afirmaciones."
        else:
            resultado = {"areas": [{"nombre": AREAS[k], "valor": v} for k, v in areas.items()],
                         "carreras": carreras[:5]}
            # La sesión guarda el perfil solo para esta cuenta del navegador.
            request.session["orientacion_estudiante_%s" % estudiante.pk] = resultado
            if matricula:
                with transaction.atomic():
                    RecomendacionVocacional.objects.filter(
                        matricula=matricula,
                        conocimientos_necesarios__startswith="[Autoevaluación de intereses]"
                    ).delete()
                    for dato in carreras[:5]:
                        carrera = Carrera.objects.filter(nombre__iexact=dato["nombre"]).order_by("pk").first()
                        if carrera is None:
                            carrera = Carrera.objects.create(nombre=dato["nombre"], descripcion=dato["descripcion"])
                        RecomendacionVocacional.objects.create(
                            matricula=matricula, carrera=carrera,
                            compatibilidad=Decimal(str(dato["afinidad"])),
                            conocimientos_necesarios="[Autoevaluación de intereses] " + dato["conocimientos"],
                            puntaje_requerido=Decimal("0.00"),  # desconocido: no se muestra como requisito
                        )
    return render(request, "OrientacionVocacional.html", {
        "preguntas": PREGUNTAS, "resultado": resultado, "error": error,
        "tiene_matricula": matricula is not None,
    })


@login_required
def comparador_carreras(request):
    catalogo = list(Carrera.objects.all().order_by("nombre", "pk")[:100])
    ids = []
    for raw in request.GET.getlist("carrera"):
        if raw.isdecimal() and int(raw) not in ids:
            ids.append(int(raw))
    ids = ids[:3]
    # El catálogo visible se limita, pero la selección se busca en toda la tabla.
    por_id = {c.pk: c for c in Carrera.objects.filter(pk__in=ids)}
    seleccionadas = [por_id[pk] for pk in ids if pk in por_id]
    estudiante = _estudiante(request.user)
    matricula = _matricula(estudiante)
    recomendaciones = {}
    if matricula and seleccionadas:
        for rec in RecomendacionVocacional.objects.filter(matricula=matricula, carrera__in=seleccionadas).order_by("-fecha"):
            recomendaciones.setdefault(rec.carrera_id, rec)
    for carrera in seleccionadas:
        carrera.recomendacion_propia = recomendaciones.get(carrera.pk)
    return render(request, "ComparadorDeCarreras.html", {
        "carreras": catalogo, "seleccionadas": seleccionadas,
        "limite": 3, "sin_seleccion": not ids,
    })


@login_required
def diagnostico_academico(request):
    estudiante = _estudiante(request.user)
    if not estudiante:
        raise PermissionDenied("Esta información pertenece al perfil estudiantil.")
    resumen = resumen_estudiante(estudiante)
    return render(request, "DiagnosticoAcademico.html", {"resumen": resumen})


@login_required
@require_http_methods(["GET", "POST"])
def plan_estudio(request):
    """Guarda y mide sesiones del propio estudiante; las semanas viejas son solo lectura."""
    estudiante = _estudiante(request.user)
    if not estudiante:
        raise PermissionDenied("Esta planificación requiere un perfil estudiantil.")
    hoy = timezone.localdate()
    semana_actual = lunes_de(hoy)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "crear":
            _, creado = crear_plan_actual(estudiante, semana_actual)
            if creado:
                messages.success(request, "Tu plan de esta semana quedó guardado.")
            else:
                messages.info(request, "Ya tienes un plan guardado esta semana; se conservaron tus avances.")
            return redirect("plan_semanal")

        if accion in ("registrar", "reabrir"):
            sesion_id = request.POST.get("sesion_id", "")
            if not sesion_id.isdecimal():
                raise Http404("Sesión no encontrada.")
            with transaction.atomic():
                sesion = get_object_or_404(
                    SesionPlanSemanal.objects.select_for_update(),
                    pk=int(sesion_id),
                    plan__estudiante=estudiante,
                    plan__semana_inicio=semana_actual,
                )
                if accion == "registrar":
                    try:
                        minutos = int(request.POST.get("minutos", ""))
                        notas = request.POST.get("notas", "").strip()
                        marcar_sesion(sesion, minutos, notas)
                    except (ValueError, TypeError) as exc:
                        messages.error(request, str(exc) if str(exc) else "Revisa los minutos de estudio.")
                    else:
                        messages.success(request, "Sesión registrada. Tu progreso se actualizó.")
                else:
                    reabrir_sesion(sesion)
                    messages.info(request, "El registro se reabrió para corregirlo.")
            return redirect("plan_semanal")
        return HttpResponseBadRequest("Acción de planificación no válida.")

    semana_seleccionada = request.GET.get("semana")
    if semana_seleccionada:
        try:
            inicio = date.fromisoformat(semana_seleccionada)
        except ValueError:
            return HttpResponseBadRequest("Fecha de semana inválida.")
        if inicio.weekday() != 0:
            return HttpResponseBadRequest("La semana debe comenzar en lunes.")
    else:
        inicio = semana_actual

    plan_guardado = PlanEstudioSemanal.objects.filter(
        estudiante=estudiante, semana_inicio=inicio
    ).first()
    progreso = resumen_plan(plan_guardado) if plan_guardado else None
    resumen = resumen_estudiante(estudiante)
    es_actual = inicio == semana_actual
    return render(request, "PlanSemanal.html", {
        "resumen": resumen,
        "plan_guardado": plan_guardado,
        "progreso": progreso,
        "semana_inicio": inicio,
        "semana_fin": inicio + timedelta(days=6),
        "es_semana_actual": es_actual,
        "hoy": hoy,
        "propuesta": plan_semanal(resumen) if es_actual and not plan_guardado else [],
        "historial": historial_semanal(estudiante),
    })


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


@login_required
def panel_acudiente(request):
    if not _tiene_rol(request.user, "ACUDIENTE"):
        raise PermissionDenied("Necesitas el rol ACUDIENTE para consultar estudiantes vinculados.")
    # No mostrar un solo estudiante ajeno: se consulta la vinculación formal.
    vinculos = EstudianteAcudiente.objects.filter(
        acudiente__persona__perfil_user__user=request.user
    ).select_related("estudiante__persona", "relacion").order_by("estudiante__persona__apellido")
    hijos = []
    for vinculo in vinculos:
        estudiante = vinculo.estudiante
        matricula = Matricula.objects.filter(estudiante=estudiante, activa=True).select_related(
            "curso__grado", "anio_lectivo"
        ).first()
        resultados = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("-fecha", "-pk")[:5])
        hijos.append({"estudiante": estudiante, "matricula": matricula,
                     "relacion": vinculo.relacion, "resultados": resultados,
                     "actividades_pendientes": ActividadAsignada.objects.filter(
                         matricula=matricula, completada=False
                     ).count() if matricula else 0})
    return render(request, "PanelAcudiente.html", {"hijos": hijos})
