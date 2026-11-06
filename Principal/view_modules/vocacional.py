"""Autoconocimiento y comparación vocacional; conserva salida descriptiva actual."""
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from Principal.models import Carrera, RecomendacionVocacional
from Principal.services.orientacion import AREAS, PREGUNTAS, calcular_perfil
from .selectores import _estudiante, _matricula

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
def comparadorDeCarreras(request):
    return render(request, "ComparadorDeCarreras.html", {
        "carreras": Carrera.objects.all().order_by("nombre")
    })

