"""Modelos del plan de estudio semanal persistente."""

from django.db import models

from .academico import Estudiante


class PlanEstudioSemanal(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="planes_semanales"
    )
    semana_inicio = models.DateField()  # Lunes de la semana
    creado_en = models.DateTimeField(auto_now_add=True)
    con_datos_academicos = models.BooleanField(default=False)

    class Meta:
        ordering = ["-semana_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "semana_inicio"],
                name="uq_plan_estudiante_semana",
            ),
        ]

    def __str__(self):
        return f"{self.estudiante} | {self.semana_inicio}"


class SesionPlanSemanal(models.Model):
    plan = models.ForeignKey(
        PlanEstudioSemanal, on_delete=models.CASCADE, related_name="sesiones"
    )
    dia_indice = models.PositiveSmallIntegerField()  # Lunes=0, domingo=6
    dia_nombre = models.CharField(max_length=12)
    fecha_programada = models.DateField()
    area = models.CharField(max_length=100)
    actividad = models.CharField(max_length=250)
    minutos_previstos = models.PositiveSmallIntegerField()
    destino = models.CharField(max_length=32, default="test")
    completada = models.BooleanField(default=False)
    minutos_realizados = models.PositiveSmallIntegerField(default=0)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    notas = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["dia_indice"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "dia_indice"],
                name="uq_sesion_plan_dia",
            ),
        ]

    def __str__(self):
        return f"{self.plan} | {self.dia_nombre}"