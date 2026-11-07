"""Repetición espaciada determinista, solo de preguntas aprobadas."""
from datetime import timedelta

from django.utils import timezone

from Principal.models import PreguntaBanco, RepasoEspaciado

INTERVALOS = (1, 3, 7, 14, 30, 60)


def registrar_resultados_repaso(estudiante, detalles):
    """Actualizar tras una calificación válida, dentro de su transacción."""
    hoy = timezone.localdate()
    ahora = timezone.now()
    for detalle in detalles:
        pregunta_id = detalle.get("id_banco")
        if not pregunta_id:
            continue
        pregunta = PreguntaBanco.objects.filter(
            pk=pregunta_id, estado="APROBADA", activo=True,
        ).first()
        if pregunta is None:
            continue
        repaso, _ = RepasoEspaciado.objects.select_for_update().get_or_create(
            estudiante=estudiante, pregunta=pregunta,
        )
        if detalle["es_correcta"]:
            repaso.aciertos_seguidos = min(repaso.aciertos_seguidos + 1, len(INTERVALOS))
        else:
            repaso.aciertos_seguidos = 0
        indice = max(0, repaso.aciertos_seguidos - 1)
        repaso.intervalo_dias = INTERVALOS[indice]
        repaso.proximo_repaso = hoy + timedelta(days=repaso.intervalo_dias)
        repaso.ultima_respuesta = ahora
        repaso.save(update_fields=[
            "aciertos_seguidos", "intervalo_dias", "proximo_repaso",
            "ultima_respuesta",
        ])


def repasos_pendientes(estudiante, limite=50):
    """Solo la versión vigente y aprobada entra en nuevos repasos."""
    return RepasoEspaciado.objects.filter(
        estudiante=estudiante,
        proximo_repaso__lte=timezone.localdate(),
        pregunta__estado="APROBADA",
        pregunta__activo=True,
    ).select_related("pregunta").order_by("proximo_repaso", "pk")[:limite]
