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


    # Banco de preguntas: dos docentes y un estudiante completamente ficticios.
    from datetime import date

    from Principal.models import (
        AnioLectivo,
        AsignacionDocenteCurso,
        Curso,
        Estudiante,
        Grado,
        Matricula,
        Persona,
        Rol,
        Sexo,
    )

    rol_docente, _ = Rol.objects.get_or_create(nombre="DOCENTE")
    rol_estudiante, _ = Rol.objects.get_or_create(nombre="ESTUDIANTE")
    grado, _ = Grado.objects.get_or_create(nombre="Once E2E")
    curso, _ = Curso.objects.get_or_create(grado=grado, nombre="E2E")
    anio, _ = AnioLectivo.objects.get_or_create(
        anio=2026,
        defaults={
            "fecha_inicio": date(2026, 1, 1),
            "fecha_fin": date(2026, 12, 31), "activo": True,
        },
    )
    for nombre in ("docente_e2e", "revisor_e2e"):
        usuario, _ = user_model.objects.get_or_create(username=nombre)
        usuario.is_active = True
        usuario.set_password("SoloPruebasE2E!2026")
        usuario.save()
        perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
        perfil.roles.add(rol_docente)
        AsignacionDocenteCurso.objects.get_or_create(
            docente=perfil, curso=curso, anio_lectivo=anio,
            defaults={"activo": True},
        )

    perfil_alumno, _ = PerfilUsuario.objects.get_or_create(user=student)
    perfil_alumno.roles.add(rol_estudiante)
    sexo, _ = Sexo.objects.get_or_create(descripcion="Prueba CI E2E")
    persona, _ = Persona.objects.get_or_create(
        perfil_user=perfil_alumno,
        defaults={
            "nombre": "Estudiante", "apellido": "E2E",
            "documento": "E2E-SINTETICO-001",
            "fecha_nacimiento": date(2009, 1, 1),
            "direccion": "Solo prueba", "telefono": "00000000",
            "sexo": sexo,
        },
    )
    alumno, _ = Estudiante.objects.get_or_create(persona=persona)
    Matricula.objects.get_or_create(
        estudiante=alumno, anio_lectivo=anio,
        defaults={"curso": curso, "activa": True},
    )


seed_e2e()
