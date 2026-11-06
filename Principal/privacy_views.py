"""Autoservicio de datos personales: acceso restringido a la propia cuenta."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import (
    ActividadAsignada, Estudiante, IntentoEvaluacion, Matricula, Persona,
    PerfilUsuario, RecomendacionVocacional, RespuestaEvaluacion,
)


@login_required
@never_cache
@require_GET
def privacidad(request):
    return render(request, "Privacidad.html")


@login_required
@never_cache
@require_GET
def exportar_mis_datos(request):
    """Exporta perfil y registros académicos propios, sin contraseñas ni claves."""
    usuario = request.user
    perfil = PerfilUsuario.objects.filter(user=usuario).first()
    persona = Persona.objects.filter(perfil_user=perfil).select_related("sexo").first() if perfil else None
    estudiante = Estudiante.objects.filter(persona=persona).first() if persona else None

    resultado = {
        "alcance": (
            "Exportación de cuenta, datos de perfil y registros académicos propios. "
            "No incluye conversaciones LangGraph, memorias vectoriales ChromaDB, "
            "adjuntos ni copias de seguridad; su gestión es independiente."
        ),
        "cuenta": {
            "usuario": usuario.username,
            "nombre": usuario.first_name,
            "apellido": usuario.last_name,
            "correo": usuario.email,
            "alta": usuario.date_joined,
            "roles": list(perfil.roles.values_list("nombre", flat=True)) if perfil else [],
        },
        "persona": {
            "nombre": persona.nombre,
            "apellido": persona.apellido,
            "documento": persona.documento,
            "fecha_nacimiento": persona.fecha_nacimiento,
            "direccion": persona.direccion,
            "telefono": persona.telefono,
            "sexo": persona.sexo.descripcion,
        } if persona else None,
        "estudiante": None,
    }

    if estudiante:
        matriculas = list(Matricula.objects.filter(estudiante=estudiante).select_related(
            "curso__grado", "anio_lectivo"
        ).order_by("-anio_lectivo__anio"))
        intentos = list(IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by("fecha", "pk"))
        actividades = ActividadAsignada.objects.filter(
            matricula__in=matriculas
        ).select_related("actividad").order_by("fecha_asignacion")
        recomendaciones = RecomendacionVocacional.objects.filter(
            matricula__in=matriculas
        ).select_related("carrera").order_by("fecha")

        resultado["estudiante"] = {
            "necesidades_especiales": estudiante.necesidades_especiales,
            "matriculas": [{
                "grado": matricula.curso.grado.nombre,
                "curso": matricula.curso.nombre,
                "anio": matricula.anio_lectivo.anio,
                "activa": matricula.activa,
            } for matricula in matriculas],
            "evaluaciones": [{
                "materia": intento.materia,
                "fecha": intento.fecha,
                "aciertos": intento.aciertos,
                "total_preguntas": intento.total_preguntas,
                "porcentaje": intento.porcentaje,
                "respuestas": list(RespuestaEvaluacion.objects.filter(
                    intento=intento
                ).order_by("numero").values(
                    "numero", "competencia", "pregunta", "respuesta_estudiante",
                    "respuesta_correcta", "es_correcta", "explicacion",
                )),
            } for intento in intentos],
            "actividades": [{
                "titulo": asignacion.actividad.titulo,
                "completada": asignacion.completada,
                "puntaje": str(asignacion.puntaje) if asignacion.puntaje is not None else None,
                "fecha_asignacion": asignacion.fecha_asignacion,
            } for asignacion in actividades],
            "recomendaciones_vocacionales": [{
                "carrera": recomendacion.carrera.nombre,
                "afinidad_orientativa": str(recomendacion.compatibilidad),
                "fecha": recomendacion.fecha,
            } for recomendacion in recomendaciones],
        }

    respuesta = JsonResponse(resultado, json_dumps_params={"ensure_ascii": False, "indent": 2})
    respuesta["Content-Disposition"] = 'attachment; filename="mis-datos-preicfes.json"'
    return respuesta
