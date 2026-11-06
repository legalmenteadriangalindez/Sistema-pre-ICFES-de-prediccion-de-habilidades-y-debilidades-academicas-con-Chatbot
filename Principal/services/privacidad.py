"""Conservación y eliminación de archivos personales fuera de la base Django."""
import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def eliminar_directorios_de_cuenta(user_id):
    """Elimina únicamente las carpetas creadas para ese ID de cuenta.

    Los archivos legacy de media/ no están atribuibles a un usuario de forma
    fiable, por lo que se conservan para un proceso administrativo de revisión.
    """
    identificador = str(int(user_id))
    raices = (
        Path(settings.PRIVATE_UPLOAD_ROOT),
        Path(settings.BASE_DIR) / "ProyectoDeGrado" / "DATABASES" / "USERS",
    )
    for raiz in raices:
        objetivo = raiz / identificador
        try:
            if objetivo.is_symlink():
                logger.warning("Carpeta de usuario simbólica no eliminada: usuario %s", identificador)
                continue
            if objetivo.exists() and objetivo.is_dir():
                shutil.rmtree(objetivo)
        except OSError:
            logger.exception("No se pudo borrar el directorio privado del usuario %s", identificador)


def eliminar_archivos_al_confirmar_cuenta(user_id):
    """Evita eliminar archivos si se revierte una transacción de borrado."""
    transaction.on_commit(lambda: eliminar_directorios_de_cuenta(user_id))
