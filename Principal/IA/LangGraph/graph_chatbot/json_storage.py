"""Lectura y escritura atómica de JSON privado (sin cambiar el esquema)."""

import json
import os
import tempfile
from pathlib import Path


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def save_json_atomic(path, value):
    """Nunca truncar el archivo existente antes de completar la escritura."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    file_handle, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(file_handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
