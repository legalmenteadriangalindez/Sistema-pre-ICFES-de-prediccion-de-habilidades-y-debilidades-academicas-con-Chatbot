"""Borradores de IA; nunca se autoaprueban ni publican."""
from django.db import transaction

from Principal.models import PreguntaBanco
from Principal.services.evaluaciones import normalizar_preguntas


def generar_borrador_ia(materia, usuario):
    """La IA solo propone un borrador, nunca lo publica sin revisión humana."""
    from Principal.services.gestion_view_test import generar_quizes

    entradas = generar_quizes(materia, 1)
    normalizadas = normalizar_preguntas(entradas, materia)
    pregunta = normalizadas[0]
    opciones = pregunta["opciones"]
    if set(opciones) != {"A", "B", "C", "D"}:
        raise ValueError("La IA no devolvió cuatro alternativas completas.")

    objeto = PreguntaBanco(
        materia=materia, competencia=pregunta["competencia"][:100],
        evidencia="",  # El revisor humano puede completar la evidencia.
        dificultad="MEDIA", contexto=pregunta["contexto"][:5000],
        enunciado=pregunta["pregunta"][:2000],
        opciones=opciones,
        respuesta_correcta=pregunta["respuesta_correcta"],
        explicacion=pregunta["explicacion"][:2000],
        origen="IA", creado_por=usuario, estado="BORRADOR",
    )
    objeto.huella = objeto.generar_huella(objeto.materia, objeto.enunciado)
    objeto.full_clean()
    with transaction.atomic():
        objeto.save()
    return objeto
