"""Operaciones sobre el plan semanal persistente, sin modelos externos de IA."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from Principal.models import PlanEstudioSemanal, SesionPlanSemanal
from Principal.services.seguimiento import plan_semanal, resumen_estudiante


def lunes_de(fecha):
    """Fecha de inicio ISO de la semana (lunes)."""
    return fecha - timedelta(days=fecha.weekday())


def crear_plan_actual(estudiante, inicio_semana):
    """Crea una sola instantánea semanal; repetir no altera sesiones existentes.

    La restricción de unicidad y la transacción impiden duplicados por
    doble envío. Una vez creado el plan se conserva aunque cambien notas.
    """
    with transaction.atomic():
        existente = PlanEstudioSemanal.objects.filter(
            estudiante=estudiante, semana_inicio=inicio_semana
        ).first()
        if existente:
            return existente, False

        resumen = resumen_estudiante(estudiante)
        propuesto = plan_semanal(resumen)
        plan, creado = PlanEstudioSemanal.objects.get_or_create(
            estudiante=estudiante,
            semana_inicio=inicio_semana,
            defaults={"con_datos_academicos": resumen["con_datos"]},
        )
        if creado:
            SesionPlanSemanal.objects.bulk_create([
                SesionPlanSemanal(
                    plan=plan,
                    dia_indice=indice,
                    dia_nombre=sesion["dia"],
                    fecha_programada=inicio_semana + timedelta(days=indice),
                    area=sesion["area"],
                    actividad=sesion["actividad"],
                    minutos_previstos=sesion["minutos"],
                    destino=sesion["link"],
                )
                for indice, sesion in enumerate(propuesto)
            ])
        return plan, creado


def resumen_plan(plan):
    """Métricas observables, no predicciones ni notas Saber 11."""
    sesiones = list(plan.sesiones.all().order_by("dia_indice"))
    total = len(sesiones)
    hechas = sum(s.completada for s in sesiones)
    minutos_objetivo = sum(s.minutos_previstos for s in sesiones)
    minutos_hechos = sum(s.minutos_realizados for s in sesiones if s.completada)
    return {
        "sesiones": sesiones,
        "total": total,
        "completadas": hechas,
        "pendientes": total - hechas,
        "porcentaje": round(100 * hechas / total) if total else 0,
        "minutos_objetivo": minutos_objetivo,
        "minutos_realizados": minutos_hechos,
        "porcentaje_tiempo": (
            min(100, round(100 * minutos_hechos / minutos_objetivo))
            if minutos_objetivo else 0
        ),
    }


def historial_semanal(estudiante, limite=8):
    """Devuelve evolución de las últimas semanas efectivamente guardadas."""
    planes = PlanEstudioSemanal.objects.filter(
        estudiante=estudiante
    ).prefetch_related("sesiones").order_by("-semana_inicio")[:limite]
    return [
        {"plan": plan, "progreso": resumen_plan(plan)}
        for plan in planes
    ]


def marcar_sesion(sesion, minutos, notas=""):
    """Registra duración y fecha reales en un solo cambio de sesión."""
    if not isinstance(minutos, int) or not 1 <= minutos <= 480:
        raise ValueError("Los minutos de estudio deben estar entre 1 y 480.")
    if len(notas) > 500:
        raise ValueError("La nota no puede superar 500 caracteres.")
    sesion.completada = True
    sesion.minutos_realizados = minutos
    sesion.fecha_completada = timezone.now()
    sesion.notas = notas
    sesion.save(update_fields=[
        "completada", "minutos_realizados", "fecha_completada", "notas"
    ])


def reabrir_sesion(sesion):
    """Permite rectificar registros del plan actual sin borrar la sesión."""
    sesion.completada = False
    sesion.minutos_realizados = 0
    sesion.fecha_completada = None
    sesion.notas = ""
    sesion.save(update_fields=[
        "completada", "minutos_realizados", "fecha_completada", "notas"
    ])
