"""Preguntas originales de inglés inspiradas en los formatos Saber 11.

Dos tipos: interpretación de avisos y completar textos. No se almacena la clave en HTML.
"""
import random

BANCO_INGLES = [
    {"tipo": "aviso", "contexto": "Notice: Please leave your bags at the front desk before entering.", "pregunta": "Where would you probably see this notice?", "opciones": {"A": "At a library", "B": "At a swimming pool", "C": "At a restaurant"}, "respuesta_correcta": "A", "explicacion": "El aviso pide dejar los bolsos en recepción antes de entrar; una biblioteca puede tener esta norma para proteger sus materiales.", "error_comun": "Relaciona las instrucciones de un aviso con el lugar donde normalmente se aplican."},
    {"tipo": "aviso", "contexto": "Notice: Wear a helmet before riding your bicycle.", "pregunta": "Where is this notice most appropriate?", "opciones": {"A": "At a cycling park", "B": "At a cinema", "C": "At a bakery"}, "respuesta_correcta": "A", "explicacion": "El casco protege al ciclista; la indicación corresponde a un espacio donde se practica ciclismo.", "error_comun": "Identifica palabras clave del aviso, como helmet y bicycle."},
    {"tipo": "aviso", "contexto": "Notice: Keep your ticket until the end of your journey.", "pregunta": "Where can you find this instruction?", "opciones": {"A": "On a bus", "B": "In a kitchen", "C": "At a gym"}, "respuesta_correcta": "A", "explicacion": "Conservar el tiquete hasta terminar el trayecto es una norma habitual del transporte público.", "error_comun": "La expresión journey se refiere a un viaje o trayecto."},
    {"tipo": "aviso", "contexto": "Notice: Do not feed the animals.", "pregunta": "Where would you see this sign?", "opciones": {"A": "At a zoo", "B": "At a bank", "C": "At a bookstore"}, "respuesta_correcta": "A", "explicacion": "No alimentar animales es una norma de protección habitual en zoológicos.", "error_comun": "Relaciona feed the animals con espacios donde se observan animales."},
    {"tipo": "aviso", "contexto": "Notice: Silence your phone during the performance.", "pregunta": "Where is this sign most likely displayed?", "opciones": {"A": "In a theater", "B": "On a football field", "C": "At a market"}, "respuesta_correcta": "A", "explicacion": "Una performance es una función o espectáculo; por eso se pide silenciar el celular en el teatro.", "error_comun": "Distingue performance de actividades deportivas o compras."},
    {"tipo": "texto", "contexto": "Emma is a student. She goes to school ___ bus every morning.", "pregunta": "Choose the word that completes the sentence.", "opciones": {"A": "by", "B": "on", "C": "at"}, "respuesta_correcta": "A", "explicacion": "Para indicar el medio de transporte se usa by + bus: by bus, sin artículo.", "error_comun": "No confundas by bus con on the bus: la primera expresa el medio de transporte."},
    {"tipo": "texto", "contexto": "Yesterday, Daniel ___ his grandparents in the countryside.", "pregunta": "Choose the correct verb form.", "opciones": {"A": "visit", "B": "visited", "C": "visiting"}, "respuesta_correcta": "B", "explicacion": "Yesterday indica pasado simple; el verbo regular visit cambia a visited.", "error_comun": "La forma visit es presente/base y visiting es gerundio, no pasado simple."},
    {"tipo": "texto", "contexto": "My sister is ___ than I am, but I am taller.", "pregunta": "Choose the correct comparative.", "opciones": {"A": "young", "B": "youngest", "C": "younger"}, "respuesta_correcta": "C", "explicacion": "Con than se necesita un adjetivo comparativo: younger.", "error_comun": "Young es grado positivo y youngest es superlativo; than requiere comparativo."},
    {"tipo": "texto", "contexto": "We stayed at home ___ it was raining heavily.", "pregunta": "Choose the best connector.", "opciones": {"A": "because", "B": "although", "C": "until"}, "respuesta_correcta": "A", "explicacion": "Because expresa la causa: se quedaron en casa porque llovía mucho.", "error_comun": "Although introduce contraste y until expresa límite temporal; aquí se pide una causa."},
    {"tipo": "texto", "contexto": "There aren't ___ apples left in the basket.", "pregunta": "Choose the correct quantifier.", "opciones": {"A": "much", "B": "many", "C": "little"}, "respuesta_correcta": "B", "explicacion": "Apples es un sustantivo contable plural; se usa many en una oración negativa.", "error_comun": "Much y little se emplean normalmente con sustantivos incontables."},
]


def generar_prueba_ingles(cantidad=10):
    """Devuelve preguntas con opciones barajadas y claves solo para el servidor."""
    if not isinstance(cantidad, int) or not 1 <= cantidad <= len(BANCO_INGLES):
        raise ValueError("Cantidad de preguntas fuera del banco disponible")
    preguntas = []
    for indice, original in enumerate(random.sample(BANCO_INGLES, cantidad)):
        alternativas = [(letra, original["opciones"][letra]) for letra in ("A", "B", "C")]
        random.shuffle(alternativas)
        opciones = {letra: texto for letra, (_, texto) in zip(("A", "B", "C"), alternativas)}
        correcta = next(letra for letra, (anterior, _) in zip(("A", "B", "C"), alternativas) if anterior == original["respuesta_correcta"])
        preguntas.append({"id": indice, "tipo": original["tipo"], "competencia": "Interpretación de avisos" if original["tipo"] == "aviso" else "Gramática y vocabulario", "contexto": original["contexto"], "pregunta": original["pregunta"], "opciones": opciones, "respuesta_correcta": correcta, "explicacion": original["explicacion"], "error_comun": original["error_comun"]})
    return preguntas
