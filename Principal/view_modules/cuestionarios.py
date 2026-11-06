"""Generación, calificación y consulta de cuestionarios por materia."""
import logging
import unicodedata

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Principal.models import Estudiante, PerfilUsuario, Persona
from Principal.services.evaluaciones import (
    calificar_y_guardar_evaluacion, normalizar_preguntas,
    preguntas_para_estudiante,
)
from Principal.services.gestion_view_test import generar_material, generar_quizes
from Principal.services.pruebas_ingles import generar_prueba_ingles

@login_required
def test(request, *, generar_quizes_func=generar_quizes, generar_material_func=generar_material):
    contexto = {"preguntas": [], "materiales_recomendados": []}
    if request.method == "POST" and (
        request.POST.get("verificar_ingles") or request.POST.get("verificar_cuestionario")
    ):
        es_ingles = bool(request.POST.get("verificar_ingles"))
        clave_sesion = "prueba_ingles_preguntas" if es_ingles else "prueba_materia_preguntas"
        pendientes = request.session.pop(clave_sesion, None)
        if not pendientes:
            contexto["error_prueba"] = "La evaluación expiró o ya fue calificada. Genera una nueva prueba."
        else:
            perfil = PerfilUsuario.objects.filter(user=request.user).first()
            persona = Persona.objects.filter(perfil_user=perfil).first()
            estudiante = Estudiante.objects.filter(persona=persona).first()
            if not estudiante:
                contexto["error_prueba"] = "Debes completar tu registro como estudiante para guardar resultados."
            else:
                materia = "Inglés" if es_ingles else str(pendientes[0].get("materia", "Evaluación"))
                resultado, detalles, competencias = calificar_y_guardar_evaluacion(
                    estudiante=estudiante,
                    materia=materia,
                    preguntas=pendientes,
                    datos_respuesta=request.POST,
                )
                contexto["materia_evaluacion"] = materia
                contexto["resultado_evaluacion"] = resultado
                contexto["detalles_evaluacion"] = detalles
                contexto["competencias_evaluacion"] = competencias
                if es_ingles:
                    # Mantener las claves de contexto ya utilizadas por el historial de inglés.
                    contexto["resultado_ingles"] = resultado
                    contexto["detalles_ingles"] = detalles
                    contexto["competencias_ingles"] = competencias
    elif request.method == "POST" and "materia" in request.POST:
        entrada = request.POST.get("materia", "").strip()
        clave_materia = "".join(
            caracter
            for caracter in unicodedata.normalize("NFKD", entrada.casefold())
            if not unicodedata.combining(caracter)
        )
        materias = {
            "lectura critica": "Lectura Crítica",
            "matematicas": "Matemáticas",
            "sociales y ciudadanas": "Sociales y Ciudadanas",
            "ciencias naturales": "Ciencias Naturales",
            "ingles": "Inglés",
        }
        materia = materias.get(clave_materia)
        if not materia:
            contexto["error_prueba"] = "Selecciona una materia válida para iniciar la evaluación."
        elif clave_materia == "ingles":
            preguntas = generar_prueba_ingles()
            request.session["prueba_ingles_preguntas"] = preguntas
            contexto["preguntas_ingles"] = preguntas_para_estudiante(preguntas)
        else:
            try:
                preguntas = normalizar_preguntas(generar_quizes_func(materia, 1), materia)
            except ValueError as error:
                contexto["error_prueba"] = str(error)
            except Exception:
                logging.getLogger(__name__).exception("Falló la generación de un cuestionario")
                contexto["error_prueba"] = (
                    "No fue posible generar el cuestionario en este momento. Intenta nuevamente."
                )
            else:
                # La clave se conserva en la sesión de Django, nunca en el HTML.
                request.session["prueba_materia_preguntas"] = [
                    {**pregunta, "materia": materia} for pregunta in preguntas
                ]
                contexto["preguntas"] = preguntas_para_estudiante(preguntas)
                try:
                    contexto["materiales_recomendados"] = generar_material_func(preguntas)
                except Exception:
                    logging.getLogger(__name__).exception(
                        "No fue posible generar materiales recomendados para la prueba"
                    )
    return render(request, "TestDeVocacion.html", contexto)
# ********************************TEST***************************************



# =============================RECOMENDACIONES======================================

