"""Importación y exportación académica con autorización por rol y curso."""
import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from Principal.models import IntentoEvaluacion, Matricula
from Principal.services.importacion_matriculas import importar_matriculas
from Principal.services.privacidad_educativa import registrar_auditoria
from .docentes import matriculas_permitidas_docente
from .selectores import _tiene_rol, es_gestor


@login_required
@require_http_methods(["GET", "POST"])
def cargar_matriculas(request):
    if not es_gestor(request.user):
        raise PermissionDenied("Solo administración puede importar matrículas.")
    if request.method == "POST":
        archivo = request.FILES.get("archivo")
        if archivo is None:
            messages.error(request, "Selecciona un archivo CSV o XLSX.")
        else:
            try:
                creadas, existentes = importar_matriculas(archivo)
            except (ValueError, OSError, TypeError) as exc:
                messages.error(request, f"No se importó ningún registro: {exc}")
                registrar_auditoria(request.user, "IMPORTACION_RECHAZADA", "Matricula")
            else:
                registrar_auditoria(request.user, "IMPORTACION_MATRICULAS", "Matricula")
                messages.success(
                    request, f"Matrículas creadas: {creadas}; ya existentes: {existentes}.",
                )
                return redirect("cargar_matriculas")
    return render(request, "ImportacionMatriculas.html")


def limpiar_csv(valor):
    """Mitigar inyección de fórmulas al abrir CSV en Excel."""
    texto = str(valor or "")
    if texto.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + texto
    return texto


@login_required
@require_GET
def exportar_reporte_matriculas(request):
    if es_gestor(request.user):
        matriculas = Matricula.objects.filter(activa=True)
    elif _tiene_rol(request.user, "DOCENTE"):
        matriculas = matriculas_permitidas_docente(request.user)
    else:
        raise PermissionDenied("Solo administración o docentes autorizados.")
    matriculas = list(matriculas.select_related(
        "estudiante__persona", "curso__grado", "anio_lectivo",
    ).order_by("curso_id", "estudiante_id")[:1500])
    ids = {m.estudiante_id for m in matriculas}
    indicadores = {
        fila["estudiante_id"]: fila
        for fila in IntentoEvaluacion.objects.filter(
            estudiante_id__in=ids,
        ).values("estudiante_id").annotate(
            aciertos=Sum("aciertos"), preguntas=Sum("total_preguntas"),
        )
    }
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "documento", "nombre", "curso", "grado", "anio",
        "aciertos", "preguntas", "porcentaje",
    ])
    for m in matriculas:
        dato = indicadores.get(m.estudiante_id, {})
        preguntas = dato.get("preguntas") or 0
        aciertos = dato.get("aciertos") or 0
        writer.writerow([
            limpiar_csv(m.estudiante.persona.documento),
            limpiar_csv(str(m.estudiante.persona)),
            limpiar_csv(m.curso.nombre),
            limpiar_csv(m.curso.grado.nombre),
            m.anio_lectivo.anio, aciertos, preguntas,
            round(100 * aciertos / preguntas, 1) if preguntas else "",
        ])
    registrar_auditoria(request.user, "EXPORTACION_ACADEMICA", "Matricula")
    response = HttpResponse(
        "\ufeff" + buffer.getvalue(), content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="reporte-preicfes.csv"'
    response["Cache-Control"] = "no-store"
    return response


@login_required
@require_GET
def descargar_plantilla_matriculas(request):
    if not es_gestor(request.user):
        raise PermissionDenied("La plantilla de administración es privada.")
    response = HttpResponse(
        "documento,curso_id,anio\n", content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="plantilla-matriculas.csv"'
    return response
