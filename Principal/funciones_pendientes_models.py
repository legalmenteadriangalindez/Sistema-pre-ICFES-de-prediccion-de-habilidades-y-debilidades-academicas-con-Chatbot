"""Repaso espaciado, notificaciones internas y trazabilidad educativa."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from .banco_models import PreguntaBanco


class RepasoEspaciado(models.Model):
    estudiante = models.ForeignKey(
        "Principal.Estudiante", on_delete=models.CASCADE,
        related_name="repasos_espaciados",
    )
    pregunta = models.ForeignKey(
        PreguntaBanco, on_delete=models.PROTECT,
        related_name="programaciones_repaso",
    )
    aciertos_seguidos = models.PositiveSmallIntegerField(default=0)
    intervalo_dias = models.PositiveIntegerField(default=1)
    proximo_repaso = models.DateField(default=timezone.localdate)
    ultima_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("proximo_repaso", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "pregunta"],
                name="unique_repaso_estudiante_pregunta",
            )
        ]


class NotificacionAcademica(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="avisos_academicos",
    )
    categoria = models.CharField(max_length=32)
    titulo = models.CharField(max_length=140)
    mensaje = models.CharField(max_length=500)
    clave = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    leida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-fecha", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "clave"], name="unique_aviso_por_usuario",
            )
        ]


class PreferenciaAvisos(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="preferencias_avisos",
    )
    recibir_avisos = models.BooleanField(default=True)
    avisos_familiares = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)


class RegistroAuditoria(models.Model):
    """Metadatos de operaciones sensibles; nunca contraseñas ni archivos."""
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="auditoria_operaciones",
    )
    accion = models.CharField(max_length=64)
    recurso = models.CharField(max_length=60)
    recurso_id = models.PositiveIntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-fecha", "-pk")


class ConsentimientoTutorIA(models.Model):
    """Declaración del acudiente vinculado para el uso de IA de un menor."""
    estudiante = models.OneToOneField(
        "Principal.Estudiante", on_delete=models.CASCADE,
        related_name="consentimiento_tutor_ia",
    )
    acudiente_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="consentimientos_tutor_ia",
    )
    autorizado = models.BooleanField(default=False)
    registrado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
