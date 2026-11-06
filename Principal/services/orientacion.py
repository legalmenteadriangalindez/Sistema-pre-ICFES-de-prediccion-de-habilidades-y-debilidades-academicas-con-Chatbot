"""Cuestionario orientativo de intereses; puntuaciones descriptivas, no psicométricas.

Sin servicios externos: la misma respuesta siempre produce el mismo perfil.
No estima salarios, admisiones ni probabilidades de éxito profesional.
"""

PREGUNTAS = (
    ("t1", "tecnologia", "Disfruto entender cómo funcionan los programas y dispositivos."),
    ("t2", "tecnologia", "Me interesa resolver problemas mediante lógica y tecnología."),
    ("t3", "tecnologia", "Me gustaría crear aplicaciones o analizar datos."),
    ("s1", "salud", "Me motiva aprender cómo funciona el cuerpo humano."),
    ("s2", "salud", "Me gustaría ayudar a mejorar la salud de otras personas."),
    ("s3", "salud", "Me interesa investigar temas de biología y bienestar."),
    ("h1", "social", "Disfruto escuchar, orientar y trabajar con otras personas."),
    ("h2", "social", "Me interesan los problemas de la comunidad y sus soluciones."),
    ("h3", "social", "Me gustaría enseñar, dialogar o mediar conflictos."),
    ("c1", "creatividad", "Disfruto diseñar, dibujar o producir contenido visual."),
    ("c2", "creatividad", "Me atrae proponer ideas originales para comunicar algo."),
    ("c3", "creatividad", "Me interesa construir proyectos artísticos o audiovisuales."),
)

AREAS = {
    "tecnologia": "Tecnología y lógica",
    "salud": "Ciencias y salud",
    "social": "Comunicación y comunidad",
    "creatividad": "Diseño y creatividad",
}

# Las carreras y descripciones son categorías exploratorias, no ofertas universitarias.
CATALOGO = (
    ("Ingeniería de Sistemas", "tecnologia", "creatividad", "Software, resolución de problemas y desarrollo de sistemas.", "Lógica, matemáticas, programación y comunicación."),
    ("Ingeniería Industrial", "tecnologia", "social", "Organización de procesos, mejora y análisis de sistemas productivos.", "Matemáticas, análisis de procesos y trabajo en equipo."),
    ("Medicina", "salud", "social", "Cuidado de la salud y estudio científico de las personas.", "Biología, química, comunicación y razonamiento científico."),
    ("Enfermería", "salud", "social", "Acompañamiento y cuidado de pacientes y comunidades.", "Biología, empatía y comunicación."),
    ("Psicología", "social", "salud", "Estudio del comportamiento humano y sus contextos.", "Comprensión lectora, escucha e investigación."),
    ("Trabajo Social", "social", "creatividad", "Intervención en comunidades y proyectos de bienestar.", "Comunicación, ciudadanía y trabajo colaborativo."),
    ("Diseño Gráfico", "creatividad", "tecnologia", "Comunicación visual, diseño y producción de piezas gráficas.", "Creatividad, expresión visual y herramientas digitales."),
    ("Comunicación Social", "creatividad", "social", "Producción y análisis de mensajes para distintos públicos.", "Lectura, redacción, análisis y comunicación."),
)


def calcular_perfil(respuestas):
    """Valida exactamente las doce respuestas 1–5 y calcula afinidades 0–100."""
    if set(respuestas) != {codigo for codigo, _, _ in PREGUNTAS}:
        raise ValueError("Responde todas las afirmaciones para obtener tu orientación.")
    acumulado = {area: [] for area in AREAS}
    for codigo, area, _ in PREGUNTAS:
        valor = str(respuestas[codigo])
        if valor not in {"1", "2", "3", "4", "5"}:
            raise ValueError("Cada respuesta debe estar entre 1 y 5.")
        acumulado[area].append(int(valor))
    # 1 = mínima afinidad (0); 5 = máxima afinidad (100).
    areas = {area: round((sum(valores) - 3) / 12 * 100, 1) for area, valores in acumulado.items()}
    carreras = []
    for nombre, principal, secundaria, descripcion, conocimientos in CATALOGO:
        afinidad = round(areas[principal] * 0.75 + areas[secundaria] * 0.25, 1)
        carreras.append({"nombre": nombre, "afinidad": afinidad, "descripcion": descripcion,
                         "conocimientos": conocimientos, "principal": AREAS[principal]})
    carreras.sort(key=lambda fila: (-fila["afinidad"], fila["nombre"]))
    return areas, carreras
