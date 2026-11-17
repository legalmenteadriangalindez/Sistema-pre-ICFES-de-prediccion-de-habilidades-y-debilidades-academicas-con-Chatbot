"""Modelos de intentos y respuestas de evaluaciones."""

from django.db import models

from .academico import Estudiante


class IntentoEvaluacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="intentos_evaluacion")
    materia = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    total_preguntas = models.PositiveIntegerField()
    aciertos = models.PositiveIntegerField()

    @property
    def porcentaje(self):
        return round(100 * self.aciertos / self.total_preguntas, 1) if self.total_preguntas else 0


class RespuestaEvaluacion(models.Model):
    pregunta_banco = models.ForeignKey(
        "PreguntaBanco", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="respuestas_evaluacion",
    )
    intento = models.ForeignKey(IntentoEvaluacion, on_delete=models.CASCADE, related_name="respuestas")
    numero = models.PositiveIntegerField()
    competencia = models.CharField(max_length=100)
    enunciado = models.TextField()
    pregunta = models.TextField()
    opciones = models.JSONField()
    respuesta_estudiante = models.CharField(max_length=1, blank=True)
    respuesta_correcta = models.CharField(max_length=1)
    explicacion = models.TextField()
    es_correcta = models.BooleanField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["intento", "numero"], name="unique_respuesta_intento_numero")]


# ========== PLAN DE ESTUDIO SEMANAL PERSISTENTE ==========
# Se conserva el plan tal como fue propuesto; las nuevas evaluaciones no
# reescriben sesiones ni avances que el estudiante ya haya registrado.