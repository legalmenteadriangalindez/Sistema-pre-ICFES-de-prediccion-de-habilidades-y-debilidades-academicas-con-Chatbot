"""Prepara exclusivamente datos ficticios para el desarrollo local.

Uso:
    python manage.py migrate
    python manage.py crear_usuarios_prueba
    python manage.py crear_usuarios_prueba --resetear-claves

No modifica cuentas ajenas a los identificadores/correos de demostración.
"""

import os
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from Principal.models import (
    Acudiente,
    AnioLectivo,
    AsignacionDocenteCurso,
    Curso,
    Estudiante,
    EstudianteAcudiente,
    Grado,
    Matricula,
    PerfilUsuario,
    Persona,
    RelacionAcudiente,
    Rol,
    Sexo,
)

CLAVE_DESARROLLO = "PreICFES2026!Demo"

# Todos los nombres, identificaciones y correos son ficticios.
CUENTAS = (
    {
        "username": "admin_demo",
        "nombre": "Admin",
        "apellido": "Demostracion",
        "rol": "ADMIN",
        "email": "admin_demo@example.test",
        "documento": "DEMO-ADMIN-001",
        "nacimiento": date(1990, 1, 15),
        "sexo": "Masculino",
        "superusuario": True,
    },
    {
        "username": "estudiante_ana",
        "nombre": "Ana",
        "apellido": "Ejemplo",
        "rol": "ESTUDIANTE",
        "email": "estudiante_ana@example.test",
        "documento": "DEMO-EST-001",
        "nacimiento": date(2009, 6, 12),
        "sexo": "Femenino",
    },
    {
        "username": "estudiante_luis",
        "nombre": "Luis",
        "apellido": "Ejemplo",
        "rol": "ESTUDIANTE",
        "email": "estudiante_luis@example.test",
        "documento": "DEMO-EST-002",
        "nacimiento": date(2008, 11, 4),
        "sexo": "Masculino",
    },
    {
        "username": "acudiente_demo",
        "nombre": "Marta",
        "apellido": "Ejemplo",
        "rol": "ACUDIENTE",
        "email": "acudiente_demo@example.test",
        "documento": "DEMO-ACU-001",
        "nacimiento": date(1983, 2, 20),
        "sexo": "Femenino",
    },
    {
        "username": "docente_demo",
        "nombre": "Carlos",
        "apellido": "Ejemplo",
        "rol": "DOCENTE",
        "email": "docente_demo@example.test",
        "documento": "DEMO-DOC-001",
        "nacimiento": date(1988, 9, 10),
        "sexo": "Masculino",
    },
)


class Command(BaseCommand):
    help = "Crea roles, personas y usuarios FICTICIOS para pruebas en modo local (DEBUG=True)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--resetear-claves",
            action="store_true",
            help="Restablece también las contraseñas de las cuentas demo ya creadas.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        demo_publico = settings.DEMO_MODE
        if not demo_publico and not settings.DEBUG:
            raise CommandError("El sembrado solo está permitido en desarrollo o demo.")
        if demo_publico and options["resetear_claves"]:
            raise CommandError("No se permite restablecer contraseñas en demo público.")

        clave = os.environ.get(
            "PREICFES_DEMO_PASSWORD",
            "" if demo_publico else CLAVE_DESARROLLO,
        )
        if len(clave) < (20 if demo_publico else 12):
            raise CommandError(
                "PREICFES_DEMO_PASSWORD debe configurarse de forma privada y "
                "tener al menos 20 caracteres en Render."
            )

        roles = {
            nombre: Rol.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": f"Rol ficticio de prueba: {nombre}"},
            )[0]
            for nombre in ("ADMIN", "ESTUDIANTE", "ACUDIENTE", "DOCENTE")
        }
        sexos = {
            nombre: Sexo.objects.get_or_create(descripcion=nombre, defaults={"activo": True})[0]
            for nombre in ("Masculino", "Femenino")
        }

        # Datos académicos mínimos para probar consultas y matrículas.
        grado, _ = Grado.objects.get_or_create(nombre="Undécimo", defaults={"activo": True})
        curso, _ = Curso.objects.get_or_create(
            grado=grado, nombre="11A", defaults={"cupo_maximo": 30, "activo": True}
        )
        anio, _ = AnioLectivo.objects.get_or_create(
            anio=2026,
            defaults={"fecha_inicio": date(2026, 1, 19), "fecha_fin": date(2026, 11, 27), "activo": True},
        )
        relacion, _ = RelacionAcudiente.objects.get_or_create(
            descripcion="Responsable de prueba", defaults={"activo": True}
        )

        User = get_user_model()
        personas = {}
        creados = 0
        restauradas = 0

        for datos in (d for d in CUENTAS if not demo_publico or not d.get("superusuario")):
            admin = datos.get("superusuario", False)
            usuario, nuevo = User.objects.get_or_create(
                username=datos["username"],
                defaults={
                    "first_name": datos["nombre"],
                    "last_name": datos["apellido"],
                    "email": datos["email"],
                    "is_active": True,  # La validación por email se reserva para registros reales.
                    "is_staff": admin,
                    "is_superuser": admin,
                },
            )
            if not nuevo and (usuario.email != datos["email"] or usuario.is_superuser != admin):
                raise CommandError(
                    f"El nombre {datos['username']} ya corresponde a otra cuenta; no se modificó."
                )
            if nuevo or options["resetear_claves"]:
                usuario.set_password(clave)  # Django aplica hash seguro, no guarda texto plano.
                if options["resetear_claves"]:
                    usuario.is_active = True
                usuario.save()
                if not nuevo:
                    restauradas += 1
            if nuevo:
                creados += 1

            perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
            perfil.roles.add(roles[datos["rol"]])
            persona, _ = Persona.objects.get_or_create(
                perfil_user=perfil,
                defaults={
                    "nombre": datos["nombre"],
                    "apellido": datos["apellido"],
                    "documento": datos["documento"],
                    "fecha_nacimiento": datos["nacimiento"],
                    "direccion": "Dirección ficticia para pruebas locales",
                    "telefono": "3000000000",
                    "sexo": sexos[datos["sexo"]],
                },
            )
            personas[datos["username"]] = persona

            if datos["rol"] == "ESTUDIANTE":
                estudiante, _ = Estudiante.objects.get_or_create(persona=persona)
                Matricula.objects.get_or_create(
                    estudiante=estudiante, anio_lectivo=anio,
                    defaults={"curso": curso, "activa": True},
                )
            elif datos["rol"] == "ACUDIENTE":
                Acudiente.objects.get_or_create(persona=persona)

        docente_demo = PerfilUsuario.objects.get(user__username="docente_demo")
        AsignacionDocenteCurso.objects.get_or_create(
            docente=docente_demo, curso=curso, anio_lectivo=anio,
            defaults={"activo": True},
        )

        acudiente = Acudiente.objects.get(persona=personas["acudiente_demo"])
        for username in ("estudiante_ana", "estudiante_luis"):
            estudiante = Estudiante.objects.get(persona=personas[username])
            EstudianteAcudiente.objects.get_or_create(
                estudiante=estudiante,
                acudiente=acudiente,
                defaults={"relacion": relacion},
            )

        self.stdout.write(self.style.SUCCESS(
            f"Datos demo preparados: {creados} usuarios nuevos; "
            f"{restauradas} contraseñas restablecidas; 2 estudiantes matriculados."
        ))
        if demo_publico:
            self.stdout.write(
                "Demo público con estudiantes y docentes ficticios. "
                "La contraseña solo está en las variables privadas de Render."
            )
        else:
            self.stdout.write("Usuarios: " + ", ".join(d["username"] for d in CUENTAS))
            self.stdout.write("Contraseña de prueba (todos): " + clave)
            self.stdout.write(self.style.WARNING(
                "Solo para desarrollo local. No reutilices esta contraseña en producción. "
                "Si ya existen, las contraseñas solo cambian con --resetear-claves."
            ))
