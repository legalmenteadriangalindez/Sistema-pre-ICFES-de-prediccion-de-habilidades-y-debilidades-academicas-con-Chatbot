"""Cuentas sintéticas: no ejecutar fuera de CI o contra otra base SQLite."""

import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model

from Principal.models import PerfilUsuario


def seed_e2e():
    database = Path(settings.DATABASES["default"]["NAME"])
    if os.environ.get("CI") != "true" or database.name != "ci-browser.sqlite3":
        raise RuntimeError("Solo se admite ci-browser.sqlite3 en CI.")

    user_model = get_user_model()
    admin, _ = user_model.objects.get_or_create(
        username="admin_e2e",
        defaults={"email": "admin-e2e@example.test", "is_staff": True, "is_superuser": True},
    )
    admin.is_staff = True
    admin.is_superuser = True
    admin.is_active = True
    admin.set_password("SoloPruebasE2E!2026")
    admin.save()
    PerfilUsuario.objects.get_or_create(user=admin)

    student, _ = user_model.objects.get_or_create(
        username="estudiante_e2e",
        defaults={"email": "estudiante-e2e@example.test"},
    )
    student.is_active = True
    student.set_password("SoloPruebasE2E!2026")
    student.save()
    PerfilUsuario.objects.get_or_create(user=student)


seed_e2e()
