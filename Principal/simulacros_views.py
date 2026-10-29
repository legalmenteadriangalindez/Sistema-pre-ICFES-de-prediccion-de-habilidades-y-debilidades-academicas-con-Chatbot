"""Simulacros cronometrados con calificación exclusivamente del lado servidor."""
import random
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Principal.models import Estudiante, IntentoEvaluacion, Persona, PerfilUsuario, RespuestaEvaluacion
from Principal.services.pruebas_ingles import generar_prueba_ingles
from Principal.services.simulacros_banco import BANCO

SESSION_KEY = "simulacro_activo"
MATERIAS = ("Matemáticas", "Lectura Crítica", "Sociales y Ciudadanas", "Ciencias Naturales", "Inglés")


def crear_preguntas(materia):
    preguntas = []
    if materia == "Integral":
        materias = MATERIAS
    else:
        materias = (materia,)
    for nombre in materias:
        if nombre == "Inglés":
            for p in generar_prueba_ingles():
                preguntas.append({"materia": nombre, "competencia": p["competencia"], "contexto": p["contexto"], "pregunta": p["pregunta"], "opciones": p["opciones"], "correcta": p["respuesta_correcta"], "explicacion": p["explicacion"]})
        else:
            for enunciado, opciones, clave, competencia, explicacion in BANCO[nombre]:
                preguntas.append({"materia": nombre, "competencia": competencia, "contexto": "", "pregunta": enunciado, "opciones": opciones, "correcta": clave, "explicacion": explicacion})
    random.shuffle(preguntas)
    for i, pregunta in enumerate(preguntas):
        pregunta["id"] = i
    return preguntas


def estudiante_actual(user):
    perfil = PerfilUsuario.objects.filter(user=user).first()
    persona = Persona.objects.filter(perfil_user=perfil).first() if perfil else None
    return Estudiante.objects.filter(persona=persona).first() if persona else None


@login_required
@require_http_methods(["GET", "POST"])
def simulacros(request):
    if request.method == "POST" and request.POST.get("accion") == "iniciar":
        materia = request.POST.get("materia")
        if materia not in (*MATERIAS, "Integral"):
            return render(request, "simulacros.html", {"materias": MATERIAS, "error": "Materia no válida."}, status=400)
        if not estudiante_actual(request.user):
            return render(request, "simulacros.html", {"materias": MATERIAS, "error": "Necesitas un perfil de estudiante."}, status=403)
        preguntas = crear_preguntas(materia)
        duracion = 3 * len(preguntas)
        request.session[SESSION_KEY] = {
            "materia": materia, "preguntas": preguntas,
            "vence": (timezone.now() + timedelta(minutes=duracion)).timestamp(),
        }
        return render(request, "simulacros.html", {"materias": MATERIAS, "simulacro": True, "preguntas": [{k:v for k,v in p.items() if k != "correcta" and k != "explicacion"} for p in preguntas], "vence": request.session[SESSION_KEY]["vence"], "duracion": duracion})
    if request.method == "POST" and request.POST.get("accion") == "finalizar":
        activo = request.session.pop(SESSION_KEY, None)
        if not activo:
            return render(request, "simulacros.html", {"materias": MATERIAS, "error": "No existe un simulacro activo."}, status=400)
        estudiante = estudiante_actual(request.user)
        if not estudiante:
            return render(request, "simulacros.html", {"materias": MATERIAS, "error": "Perfil de estudiante no encontrado."}, status=403)
        vencido = timezone.now().timestamp() > activo["vence"]
        if timezone.now().timestamp() > activo["vence"] + 15:
            return render(request, "simulacros.html", {"materias": MATERIAS, "error": "Se agotó el tiempo para enviar el simulacro. No se guardó este intento."}, status=400)
        detalles = []
        for p in activo["preguntas"]:
            respuesta = request.POST.get("respuesta_" + str(p["id"]), "")
            if respuesta not in p["opciones"]:
                respuesta = ""
            detalles.append({**p, "respuesta": respuesta, "acierto": respuesta == p["correcta"]})
        aciertos = sum(p["acierto"] for p in detalles)
        with transaction.atomic():
            intento = IntentoEvaluacion.objects.create(estudiante=estudiante, materia="Simulacro: " + activo["materia"], total_preguntas=len(detalles), aciertos=aciertos)
            RespuestaEvaluacion.objects.bulk_create([
                RespuestaEvaluacion(intento=intento, numero=p["id"], competencia=p["materia"] + " · " + p["competencia"], enunciado=p["contexto"], pregunta=p["pregunta"], opciones=p["opciones"], respuesta_estudiante=p["respuesta"], respuesta_correcta=p["correcta"], explicacion=p["explicacion"], es_correcta=p["acierto"])
                for p in detalles
            ])
        return render(request, "simulacros.html", {"materias": MATERIAS, "resultado": {"aciertos": aciertos, "total": len(detalles), "vencido": vencido, "id": intento.pk}, "detalles": detalles})
    activo = request.session.get(SESSION_KEY)
    if activo and timezone.now().timestamp() <= activo["vence"]:
        return render(request, "simulacros.html", {"materias": MATERIAS, "simulacro": True, "preguntas": [{k:v for k,v in p.items() if k not in ("correcta", "explicacion")} for p in activo["preguntas"]], "vence": activo["vence"]})
    if activo:
        request.session.pop(SESSION_KEY, None)
    return render(request, "simulacros.html", {"materias": MATERIAS})
