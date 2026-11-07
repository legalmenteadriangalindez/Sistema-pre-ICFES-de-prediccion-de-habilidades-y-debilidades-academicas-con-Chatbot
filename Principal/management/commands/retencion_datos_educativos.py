"""Retención de metadatos, ejecutada manualmente y sin borrar notas o alumnos."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Principal.models import NotificacionAcademica, RegistroAuditoria


class Command(BaseCommand):
    help = "Mostrar o aplicar la retención de auditoría y avisos antiguos."

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true")
        parser.add_argument("--dias-auditoria", type=int, default=365)
        parser.add_argument("--dias-avisos", type=int, default=180)

    def handle(self, *args, **options):
        dias_auditoria = options["dias_auditoria"]
        dias_avisos = options["dias_avisos"]
        if not 30 <= dias_auditoria <= 3650 or not 30 <= dias_avisos <= 3650:
            raise ValueError("Los plazos deben estar entre 30 y 3650 días.")
        ahora = timezone.now()
        auditorias = RegistroAuditoria.objects.filter(
            fecha__lt=ahora - timedelta(days=dias_auditoria),
        )
        avisos = NotificacionAcademica.objects.filter(
            fecha__lt=ahora - timedelta(days=dias_avisos),
        )
        cantidad_auditoria = auditorias.count()
        cantidad_avisos = avisos.count()
        if not options["aplicar"]:
            self.stdout.write(
                f"Vista previa: {cantidad_auditoria} auditorías y "
                f"{cantidad_avisos} avisos vencerían. Usa --aplicar."
            )
            return
        auditorias.delete()
        avisos.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Depurados: {cantidad_auditoria} auditorías y {cantidad_avisos} avisos."
        ))
