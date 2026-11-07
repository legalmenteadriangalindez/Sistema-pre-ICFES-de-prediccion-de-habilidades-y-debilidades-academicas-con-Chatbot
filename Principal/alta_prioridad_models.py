"""Modelos adicionales de simulacro persistente e intervención docente."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .banco_models import PreguntaBanco


class SimulacroAvanzado(models.Model):
    """Cuestionario original de práctica, dos bloques, guardado en servidor."""
    ESTADOS = (
        ("EN_CURSO", "En curso"),
        ("PAUSADO", "En pausa"),
        ("FINALIZADO", "Finalizado"),
    )
    estudiante = models.ForeignKey(
        "Principal.Estudiante", on_delete=models.CASCADE,
        related_name="simulacros_avanzados",
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default="EN_CURSO")
    bloque = models.PositiveSmallIntegerField(default=1)
    preguntas = models.JSONField(default=list)
    respuestas = models.JSONField(default=dict)
    restantes_segundos = models.PositiveIntegerField(default=4500)
    vence_en = models.DateTimeField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    finalizado_en = models.DateTimeField(null=True, blank=True)
    intento = models.OneToOneField(
        "Principal.IntentoEvaluacion", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="simulacro_avanzado",
    )

    class Meta:
        ordering = ("-creado_en", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante"],
                condition=models.Q(estado__in=["EN_CURSO", "PAUSADO"]),
                name="unique_simu_avanzado_activo_estudiante",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.bloque not in (1, 2):
            raise ValidationError("El bloque de simulacro debe ser 1 o 2.")
        super().save(*args, **kwargs)


class IntervencionAcademica(models.Model):
    ESTADOS = (("ACTIVA", "Activa"), ("CERRADA", "Cerrada"))
    matricula = models.ForeignKey(
        "Principal.Matricula", on_delete=models.PROTECT,
        related_name="intervenciones_academicas",
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="intervenciones_asignadas",
    )
    materia = models.CharField(max_length=32, choices=PreguntaBanco.MATERIAS)
    competencia = models.CharField(max_length=100)
    objetivo = models.CharField(max_length=250)
    actividades = models.TextField(max_length=2000)
    fecha_revision = models.DateField()
    estado = models.CharField(max_length=8, choices=ESTADOS, default="ACTIVA")
    observacion_cierre = models.TextField(max_length=2000, blank=True)
    creado_en = models.DateTimeField(default=timezone.now)
    cerrado_en = models.DateTimeField(null=True, blank=True)
    # Descriptivo: puede ser None por falta de evidencias, no imputar cero.
    aciertos_inicial = models.PositiveIntegerField(default=0)
    total_inicial = models.PositiveIntegerField(default=0)
    aciertos_final = models.PositiveIntegerField(null=True, blank=True)
    total_final = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("-creado_en", "-pk")

    @property
    def porcentaje_inicial(self):
        return round(100 * self.aciertos_inicial / self.total_inicial, 1) if self.total_inicial else None

    @property
    def porcentaje_final(self):
        return (
            round(100 * self.aciertos_final / self.total_final, 1)
            if self.total_final else None
        )

    @property
    def variacion_pp(self):
        previo = self.porcentaje_inicial
        posterior = self.porcentaje_final
        return round(posterior - previo, 1) if previo is not None and posterior is not None else None
