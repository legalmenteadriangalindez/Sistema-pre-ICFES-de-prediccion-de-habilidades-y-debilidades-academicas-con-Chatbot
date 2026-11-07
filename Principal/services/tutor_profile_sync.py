"""Sincronización explícita de perfiles académicos tras un mensaje exitoso.

Nunca invocar desde la carga GET de la portada. No modifica el JSON de
memoria: conserva el contrato de perfiles de la fase 5.
"""

import logging

from django.db import transaction

from Principal.services.services_view_home import (
    get_records,
    set_AnalisisCognitivo,
    set_EstiloAprendizaje,
    set_PerfilPedagogico,
    set_RitmoAprendizaje,
)

logger = logging.getLogger(__name__)


def seleccionar_perfil_cognitivo(registros, user_id):
    """Acepta el JSON histórico en formato objeto o lista, solo del usuario."""
    if isinstance(registros, list):
        registros = next(
            (
                item
                for item in reversed(registros)
                if isinstance(item, dict)
                and str(item.get("user_id")) == str(user_id)
            ),
            None,
        )
    if not isinstance(registros, dict):
        return None
    if registros.get("user_id") is not None and str(registros["user_id"]) != str(
        user_id
    ):
        return None
    if not isinstance(registros.get("general_level"), str) or not registros[
        "general_level"
    ].strip():
        return None
    for campo in ("strong_areas", "weak_areas", "frequent_mistakes"):
        if not isinstance(registros.get(campo), list) or not all(
            isinstance(valor, str) for valor in registros[campo]
        ):
            return None
    if "area" not in registros:
        return None
    return registros


def sincronizar_perfil_academico(estudiante, registros, user_id):
    """Persiste pedagógico y cognitivo solo tras POST con respuesta satisfactoria.

    La transacción evita un perfil actualizado sin su análisis correspondiente.
    Los fallos no deben impedir que el estudiante reciba la respuesta del tutor.
    """
    if estudiante is None:
        return False
    registro = seleccionar_perfil_cognitivo(registros, user_id)
    if registro is None:
        return False
    try:
        with transaction.atomic():
            nivel, _area, fuertes, debiles, errores = get_records(registro)
            ritmo = set_RitmoAprendizaje("Medio", "Desde JSON")
            estilo = set_EstiloAprendizaje("Visual", "Desde JSON")
            set_PerfilPedagogico(estudiante, ritmo, estilo, nivel)
            set_AnalisisCognitivo(estudiante, nivel, fuertes, debiles, errores)
        return True
    except Exception as exc:
        logger.warning(
            "tutor_profile_sync_failed",
            extra={"component": "academic_profile", "error_type": type(exc).__name__},
        )
        return False
