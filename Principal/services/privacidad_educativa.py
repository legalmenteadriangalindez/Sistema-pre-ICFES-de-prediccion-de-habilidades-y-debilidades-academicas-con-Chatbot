"""Privacidad: consentimiento vinculado, auditoría mínima y retención."""
from datetime import timedelta

from django.utils import timezone

from Principal.models import (
    ConsentimientoTutorIA, RegistroAuditoria,
)


def es_menor(estudiante):
    if estudiante is None:
        return False
    nacimiento = estudiante.persona.fecha_nacimiento
    hoy = timezone.localdate()
    return (hoy.year - nacimiento.year - (
        (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day)
    )) < 18


def tutor_autorizado(estudiante):
    """Para menores, autorización explícita de un acudiente aún vinculado."""
    if not es_menor(estudiante):
        return True
    return ConsentimientoTutorIA.objects.filter(
        estudiante=estudiante, autorizado=True,
        acudiente_usuario__perfilusuario__persona__acudiente__estudianteacudiente__estudiante=estudiante,
    ).exists()


def registrar_auditoria(actor, accion, recurso, recurso_id=None):
    """No guardar IP, texto libre, claves o documentos personales."""
    return RegistroAuditoria.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        accion=accion[:64], recurso=recurso[:60],
        recurso_id=recurso_id,
    )


def expirar_auditoria(dias=365):
    """Operación explícita de mantenimiento; no se ejecuta al importar módulos."""
    limite = timezone.now() - timedelta(days=dias)
    return RegistroAuditoria.objects.filter(fecha__lt=limite).delete()[0]
