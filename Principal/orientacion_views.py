"""Orientación vocacional exploratoria y plan de estudio por datos observados."""
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Carrera, IntentoEvaluacion, Matricula, RecomendacionVocacional
from .simulacros_views import estudiante_actual
from .services.seguimiento_academico import plan_semanal, resumen_de_intentos


PREGUNTAS_VOCACIONALES = (
    ('t1', 'Disfruto resolver problemas usando computadores o tecnología.', 'tecnologia'),
    ('t2', 'Me interesa analizar datos y encontrar patrones.', 'tecnologia'),
    ('t3', 'Me gusta construir o mejorar herramientas digitales.', 'tecnologia'),
    ('s1', 'Me interesa comprender el cuerpo humano y su salud.', 'salud'),
    ('s2', 'Me motiva ayudar a personas en contextos de bienestar.', 'salud'),
    ('s3', 'Me gustaría investigar asuntos relacionados con la salud.', 'salud'),
    ('h1', 'Me interesa escuchar y comprender la conducta humana.', 'humanidades'),
    ('h2', 'Disfruto colaborar y mediar en problemas sociales.', 'humanidades'),
    ('h3', 'Me llaman la atención las ciencias sociales y la educación.', 'humanidades'),
    ('c1', 'Me gusta dibujar, diseñar o crear composiciones visuales.', 'creatividad'),
    ('c2', 'Disfruto comunicar ideas mediante imágenes y narrativas.', 'creatividad'),
    ('c3', 'Me gustaría trabajar en proyectos creativos.', 'creatividad'),
)

CARRERAS_ORIENTATIVAS = (
    ('Ingeniería de Sistemas', 'tecnologia', 'Programación, lógica y matemáticas. Estudia las tecnologías y sus aplicaciones.'),
    ('Medicina', 'salud', 'Biología, química y cuidado de las personas. Requiere formación universitaria y práctica clínica.'),
    ('Psicología', 'humanidades', 'Comunicación, investigación y comportamiento humano.'),
    ('Diseño Gráfico', 'creatividad', 'Comunicación visual, creatividad y uso de herramientas de diseño.'),
)


def matricula_actual(user):
    estudiante = estudiante_actual(user)
    if estudiante is None:
        return None
    return Matricula.objects.filter(estudiante=estudiante, activa=True).order_by('-anio_lectivo__anio').first()


@login_required
@require_http_methods(['GET', 'POST'])
def orientacion_vocacional(request):
    matricula = matricula_actual(request.user)
    if matricula is None:
        return render(request, 'orientacion_vocacional.html', {
            'preguntas': PREGUNTAS_VOCACIONALES,
            'error': 'Necesitas una matrícula activa para guardar tu orientación vocacional.',
        }, status=403)
    if request.method == 'POST':
        respuestas = {}
        for clave, _, categoria in PREGUNTAS_VOCACIONALES:
            respuesta = str(request.POST.get(clave, '')).strip()
            if respuesta not in {'1', '2', '3', '4', '5'}:
                return render(request, 'orientacion_vocacional.html', {
                    'preguntas': PREGUNTAS_VOCACIONALES,
                    'error': 'Responde las 12 afirmaciones con un número del 1 al 5.',
                }, status=400)
            respuestas[clave] = int(respuesta)
        totales = {}
        for clave, _, categoria in PREGUNTAS_VOCACIONALES:
            totales.setdefault(categoria, []).append(respuestas[clave])
        resultados = {k: round(25 * (sum(v) / len(v) - 1), 1) for k, v in totales.items()}
        with transaction.atomic():
            for nombre, categoria, descripcion in CARRERAS_ORIENTATIVAS:
                carrera, _ = Carrera.objects.get_or_create(nombre=nombre, defaults={'descripcion': descripcion})
                actualizaciones = {
                    'compatibilidad': Decimal(str(resultados[categoria])),
                    'conocimientos_necesarios': descripcion,
                    'puntaje_requerido': Decimal('0'),  # No hay puntaje de admisión verificable.
                }
                existentes = RecomendacionVocacional.objects.filter(matricula=matricula, carrera=carrera)
                if existentes.exists():
                    existentes.update(**actualizaciones)
                else:
                    RecomendacionVocacional.objects.create(matricula=matricula, carrera=carrera, **actualizaciones)
        return render(request, 'orientacion_vocacional.html', {
            'preguntas': PREGUNTAS_VOCACIONALES, 'resultados': resultados,
            'carreras': RecomendacionVocacional.objects.filter(matricula=matricula).select_related('carrera').order_by('-compatibilidad'),
            'guardado': True,
        })
    return render(request, 'orientacion_vocacional.html', {
        'preguntas': PREGUNTAS_VOCACIONALES,
        'carreras': RecomendacionVocacional.objects.filter(matricula=matricula).select_related('carrera').order_by('-compatibilidad'),
    })


@login_required
def plan_estudio(request):
    estudiante = estudiante_actual(request.user)
    if not estudiante:
        return render(request, 'plan_semanal.html', {'error': 'Esta vista requiere un perfil de estudiante.'}, status=403)
    intentos = IntentoEvaluacion.objects.filter(estudiante=estudiante).order_by('-fecha')[:120]
    resumen = resumen_de_intentos(intentos)
    return render(request, 'plan_semanal.html', {
        'resumen': resumen, 'plan': plan_semanal(resumen),
        'total_evaluaciones': IntentoEvaluacion.objects.filter(estudiante=estudiante).count(),
    })


@login_required
def comparador_carreras(request):
    carreras = Carrera.objects.all().order_by('nombre')
    seleccion = request.GET.getlist('carrera')
    if len(seleccion) > 3 or any(not x.isdecimal() for x in seleccion):
        return HttpResponseBadRequest('Selecciona hasta tres carreras válidas.')
    elegidas = carreras.filter(pk__in=seleccion)
    matricula = matricula_actual(request.user)
    afinidades = {
        r.carrera_id: r.compatibilidad
        for r in RecomendacionVocacional.objects.filter(matricula=matricula)
    } if matricula else {}
    columnas = [{'carrera': carrera, 'afinidad': afinidades.get(carrera.pk)} for carrera in elegidas]
    return render(request, 'ComparadorDeCarreras.html', {
        'carreras': carreras, 'comparadas': columnas,
        'evaluacion_disponible': bool(afinidades),
    })
