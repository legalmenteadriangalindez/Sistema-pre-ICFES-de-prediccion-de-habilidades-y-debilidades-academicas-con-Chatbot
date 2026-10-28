"""Preguntas originales de inglés inspiradas en los formatos Saber 11.

Dos tipos: interpretación de avisos y completar textos. No se almacena la clave en HTML.
"""
import random

BANCO_INGLES = [
    {"tipo": "aviso", "contexto": "Notice: Please leave your bags at the front desk before entering.", "pregunta": "Where would you probably see this notice?", "opciones": {"A": "At a library", "B": "At a swimming pool", "C": "At a restaurant"}, "respuesta_correcta": "A"},
    {"tipo": "aviso", "contexto": "Notice: Wear a helmet before riding your bicycle.", "pregunta": "Where is this notice most appropriate?", "opciones": {"A": "At a cycling park", "B": "At a cinema", "C": "At a bakery"}, "respuesta_correcta": "A"},
    {"tipo": "aviso", "contexto": "Notice: Keep your ticket until the end of your journey.", "pregunta": "Where can you find this instruction?", "opciones": {"A": "On a bus", "B": "In a kitchen", "C": "At a gym"}, "respuesta_correcta": "A"},
    {"tipo": "aviso", "contexto": "Notice: Do not feed the animals.", "pregunta": "Where would you see this sign?", "opciones": {"A": "At a zoo", "B": "At a bank", "C": "At a bookstore"}, "respuesta_correcta": "A"},
    {"tipo": "aviso", "contexto": "Notice: Silence your phone during the performance.", "pregunta": "Where is this sign most likely displayed?", "opciones": {"A": "In a theater", "B": "On a football field", "C": "At a market"}, "respuesta_correcta": "A"},
    {"tipo": "texto", "contexto": "Emma is a student. She goes to school ___ bus every morning.", "pregunta": "Choose the word that completes the sentence.", "opciones": {"A": "by", "B": "on", "C": "at"}, "respuesta_correcta": "A"},
    {"tipo": "texto", "contexto": "Yesterday, Daniel ___ his grandparents in the countryside.", "pregunta": "Choose the correct verb form.", "opciones": {"A": "visit", "B": "visited", "C": "visiting"}, "respuesta_correcta": "B"},
    {"tipo": "texto", "contexto": "My sister is ___ than I am, but I am taller.", "pregunta": "Choose the correct comparative.", "opciones": {"A": "young", "B": "youngest", "C": "younger"}, "respuesta_correcta": "C"},
    {"tipo": "texto", "contexto": "We stayed at home ___ it was raining heavily.", "pregunta": "Choose the best connector.", "opciones": {"A": "because", "B": "although", "C": "until"}, "respuesta_correcta": "A"},
    {"tipo": "texto", "contexto": "There aren't ___ apples left in the basket.", "pregunta": "Choose the correct quantifier.", "opciones": {"A": "much", "B": "many", "C": "little"}, "respuesta_correcta": "B"},
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
        preguntas.append({"id": indice, "tipo": original["tipo"], "contexto": original["contexto"], "pregunta": original["pregunta"], "opciones": opciones, "respuesta_correcta": correcta})
    return preguntas
