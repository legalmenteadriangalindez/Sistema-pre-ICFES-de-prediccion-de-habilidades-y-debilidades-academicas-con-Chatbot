"""Acceso docente por curso/año: actividades, informes y retroalimentación."""
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from Principal.models import (
    Actividad, ActividadAsignada, AsignacionDocenteCurso, IntentoEvaluacion,
    Matricula, NivelAprendizaje, RetroalimentacionDocente, Tema,
)
from .selectores import _tiene_rol
from Principal.services.avisos_academicos import avisar_retro_familiar, emitir_aviso


def matriculas_permitidas_docente(user):
    """La autorización utiliza siempre la pareja curso/año, no filtros separados."""
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


class EditarActividadDocenteForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ("titulo", "descripcion", "tema", "nivel", "activo")
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "tema": forms.Select(attrs={"class": "form-select"}),
            "nivel": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_descripcion(self):
        texto = self.cleaned_data["descripcion"].strip()
        if not texto or len(texto) > 2500:
            raise forms.ValidationError("La descripción debe contener entre 1 y 2500 caracteres.")
        return texto

    def clean_tema(self):
        tema = self.cleaned_data["tema"]
        if not tema.activo:
            raise forms.ValidationError("El tema no está activo.")
        return tema

    def clean_nivel(self):
        nivel = self.cleaned_data["nivel"]
        if not nivel.activo:
            raise forms.ValidationError("El nivel no está activo.")
        return nivel


def _verificar_rol(user):
    if not _tiene_rol(user, "DOCENTE"):
        raise PermissionDenied("Necesitas el rol DOCENTE.")


@login_required
@require_http_methods(["GET", "POST"])
def panel_docente(request):
    _verificar_rol(request.user)
    permitidas = matriculas_permitidas_docente(request.user)
    tiene_cursos = permitidas.exists()
    error, exito = None, None

    if request.method == "POST":
        if not tiene_cursos:
            raise PermissionDenied("El administrador debe asignarte un curso antes de gestionar actividades.")
        accion = request.POST.get("accion", "asignar")
        if accion == "crear":
            titulo = request.POST.get("titulo", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tema_id = request.POST.get("tema", "")
            nivel_id = request.POST.get("nivel", "")
            tema = Tema.objects.filter(pk=int(tema_id), activo=True).first() if tema_id.isdecimal() else None
            nivel = NivelAprendizaje.objects.filter(pk=int(nivel_id), activo=True).first() if nivel_id.isdecimal() else None
            if not titulo or len(titulo) > 100 or not descripcion or len(descripcion) > 2500 or not tema or not nivel:
                error = "Completa título, descripción, tema y nivel válidos para crear la actividad."
            else:
                Actividad.objects.create(
                    titulo=titulo, descripcion=descripcion, tema=tema, nivel=nivel,
                    creado_por=request.user,
                )
                exito = "Actividad creada en el catálogo. Ahora puedes asignarla."
        elif accion in ("", "asignar"):
            raw_matricula = request.POST.get("matricula", "")
            raw_actividad = request.POST.get("actividad", "")
            if not raw_matricula.isdecimal() or not raw_actividad.isdecimal():
                error = "Selecciona una matrícula y una actividad válidas."
            else:
                matricula = permitidas.filter(pk=int(raw_matricula)).first()
                if matricula is None:
                    raise PermissionDenied("No tienes acceso a la matrícula seleccionada.")
                actividad = Actividad.objects.filter(pk=int(raw_actividad), activo=True).first()
                if actividad is None:
                    error = "La actividad seleccionada no está disponible."
                else:
                    _, creada = ActividadAsignada.objects.get_or_create(
                        matricula=matricula, actividad=actividad,
                        defaults={"asignada_por": request.user},
                    )
                    exito = "Actividad asignada correctamente." if creada else "Esa actividad ya estaba asignada."
        elif accion == "retirar":
            raw = request.POST.get("asignacion_id", "")
            asignada = ActividadAsignada.objects.filter(
                pk=int(raw) if raw.isdecimal() else 0, matricula__in=permitidas,
                asignada_por=request.user,
            ).first()
            if asignada is None:
                raise PermissionDenied("Solo puedes retirar tus asignaciones en cursos autorizados.")
            if asignada.completada:
                error = "No puedes retirar una actividad que el estudiante ya completó."
            else:
                asignada.delete()
                return redirect("panel_docente")
        elif accion == "retroalimentar":
            raw = request.POST.get("matricula", "")
            texto = request.POST.get("texto", "").strip()
            matricula = permitidas.filter(pk=int(raw) if raw.isdecimal() else 0).first()
            if matricula is None:
                raise PermissionDenied("No puedes comentar sobre alumnos de otros cursos.")
            if not 10 <= len(texto) <= 1000:
                error = "La retroalimentación debe tener entre 10 y 1000 caracteres."
            else:
                comentario = RetroalimentacionDocente.objects.create(
                    matricula=matricula, docente=request.user, texto=texto,
                )
                emitir_aviso(
                    matricula.estudiante.persona.perfil_user.user,
                    "RETROALIMENTACION", "Nueva retroalimentación docente",
                    "Tienes una nueva observación docente sobre tus actividades.",
                    f"retroalimentacion-{comentario.pk}",
                )
                avisar_retro_familiar(matricula.estudiante, comentario.pk)
                exito = "Retroalimentación guardada y disponible para el estudiante."
        else:
            error = "La acción solicitada no está permitida."

    matriculas = list(permitidas.select_related(
        "estudiante__persona", "curso__grado", "anio_lectivo"
    ).order_by("curso__grado__nombre", "curso__nombre", "estudiante__persona__apellido")[:200])
    ids = [m.estudiante_id for m in matriculas]
    acumulados = {
        fila["estudiante_id"]: fila
        for fila in IntentoEvaluacion.objects.filter(estudiante_id__in=ids)
        .values("estudiante_id")
        .annotate(intentos=Count("id"), aciertos=Sum("aciertos"), preguntas=Sum("total_preguntas"))
    }
    resultados = []
    for matricula in matriculas:
        datos = acumulados.get(matricula.estudiante_id, {})
        total = datos.get("preguntas") or 0
        resultados.append({
            "matricula": matricula,
            "intentos": datos.get("intentos", 0),
            "promedio": round(100 * (datos.get("aciertos") or 0) / total, 1) if total else None,
        })

    actividades = Actividad.objects.filter(activo=True).select_related(
        "tema", "nivel"
    ).order_by("titulo")[:150]
    recientes = ActividadAsignada.objects.filter(
        matricula__in=permitidas
    ).select_related("matricula__estudiante__persona", "actividad").order_by("-fecha_asignacion")[:15]
    propias = Actividad.objects.filter(creado_por=request.user).select_related(
        "tema", "nivel"
    ).order_by("-pk")[:50]
    mis_asignaciones = ActividadAsignada.objects.filter(
        asignada_por=request.user, matricula__in=permitidas,
    ).select_related("matricula__estudiante__persona", "actividad").order_by("-fecha_asignacion")[:30]
    cursos = permitidas.values(
        "curso__grado__nombre", "curso__nombre", "anio_lectivo__anio"
    ).annotate(estudiantes=Count("estudiante_id", distinct=True)).order_by(
        "curso__grado__nombre", "curso__nombre", "anio_lectivo__anio"
    )
    return render(request, "PanelDocente.html", {
        "matriculas": matriculas, "actividades_catalogo": actividades,
        "recientes": recientes, "error": error, "exito": exito,
        "tiene_cursos": tiene_cursos, "mis_actividades": propias,
        "mis_asignaciones": mis_asignaciones, "resultados_alumnos": resultados,
        "resumen_cursos": cursos,
        "temas": Tema.objects.filter(activo=True).select_related("materia").order_by("materia__nombre", "nombre")[:150],
        "niveles": NivelAprendizaje.objects.filter(activo=True).order_by("nombre"),
    })


@login_required
@require_http_methods(["GET", "POST"])
def editar_actividad_docente(request, actividad_id):
    _verificar_rol(request.user)
    if not matriculas_permitidas_docente(request.user).exists():
        raise PermissionDenied("Debes tener al menos un curso autorizado.")
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    if not request.user.is_superuser and actividad.creado_por_id != request.user.pk:
        raise PermissionDenied("Solo puedes editar actividades creadas por ti.")
    if ActividadAsignada.objects.filter(actividad=actividad, completada=True).exists():
        raise PermissionDenied("Una actividad ya completada no puede modificarse.")
    formulario = EditarActividadDocenteForm(
        request.POST if request.method == "POST" else None, instance=actividad
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        return redirect("panel_docente")
    return render(request, "EditarActividadDocente.html", {
        "formulario": formulario, "actividad": actividad,
    })


@login_required
@require_http_methods(["GET"])
def detalle_estudiante_docente(request, matricula_id):
    _verificar_rol(request.user)
    matricula = get_object_or_404(
        matriculas_permitidas_docente(request.user).select_related("estudiante__persona", "curso", "anio_lectivo"),
        pk=matricula_id,
    )
    intentos = list(IntentoEvaluacion.objects.filter(
        estudiante=matricula.estudiante
    ).order_by("-fecha")[:30])
    asignaciones = ActividadAsignada.objects.filter(
        matricula=matricula
    ).select_related("actividad").order_by("-fecha_asignacion")
    comentarios = RetroalimentacionDocente.objects.filter(
        matricula=matricula
    ).select_related("docente")[:30]
    return render(request, "DetalleEstudianteDocente.html", {
        "matricula": matricula, "intentos": intentos,
        "asignaciones": asignaciones, "comentarios": comentarios,
    })
