"""Indicadores descriptivos y plan semanal reproducible a partir de evaluaciones.

No es un modelo de ML ni una probabilidad clínica/académica calibrada.
"""
from collections import defaultdict

AREAS = (
    'Matemáticas', 'Lectura Crítica', 'Sociales y Ciudadanas',
    'Ciencias Naturales', 'Inglés',
)


def normalizar_area(materia):
    materia = str(materia or '').removeprefix('Simulacro: ').strip()
    return materia if materia in AREAS else None


def resumen_de_intentos(intentos):
    """Recibe intentos (cada uno con materia, total_preguntas y aciertos).

    Calcula porcentajes según total de respuestas, no media de medias.
    """
    acumulados = defaultdict(list)
    for intento in intentos:
        area = normalizar_area(intento.materia)
        if area and intento.total_preguntas:
            acumulados[area].append((intento.aciertos, intento.total_preguntas))
    resultado = []
    for area in AREAS:
        lista = acumulados.get(area, [])
        correctas = sum(x for x, _ in lista)
        totales = sum(y for _, y in lista)
        porcentaje = round(100 * correctas / totales, 1) if totales else None
        if porcentaje is None:
            nivel, razon = 'Sin datos', 'Realiza una evaluación para obtener información.'
        elif totales < 10:
            nivel, razon = 'Datos limitados', 'Se necesitan más respuestas para evaluar una tendencia.'
        elif porcentaje < 60:
            nivel, razon = 'Priorizar repaso', 'Porcentaje observado inferior al 60 %.'
        elif porcentaje < 80:
            nivel, razon = 'En desarrollo', 'Reforzar contenidos y practicar nuevamente.'
        else:
            nivel, razon = 'Fortaleza observada', 'Buen porcentaje de respuestas correctas en las prácticas.'
        resultado.append({
            'area': area, 'aciertos': correctas, 'preguntas': totales,
            'porcentaje': porcentaje, 'nivel': nivel, 'razon': razon,
        })
    return resultado


def plan_semanal(resumen):
    """Sugerencias transparentes, no horarios ni asignaciones institucionales."""
    ranking = sorted(resumen, key=lambda x: (x['porcentaje'] is not None, x['porcentaje'] if x['porcentaje'] is not None else 0))
    tareas = []
    dias = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes')
    for dia, area in zip(dias, ranking):
        tareas.append({
            'dia': dia, 'area': area['area'], 'minutos': 35 if area['porcentaje'] is None or area['porcentaje'] < 60 else 25,
            'actividad': 'Repasar conceptos y resolver preguntas nuevas' if area['porcentaje'] is None or area['porcentaje'] < 80 else 'Practicar y comprobar lo aprendido',
            'motivo': area['razon'],
        })
    tareas.append({'dia': 'Sábado', 'area': 'Simulacro integral', 'minutos': 60,
                  'actividad': 'Realizar una práctica y revisar explicaciones',
                  'motivo': 'Comprobar avances sin modificar las tareas institucionales.'})
    return tareas
