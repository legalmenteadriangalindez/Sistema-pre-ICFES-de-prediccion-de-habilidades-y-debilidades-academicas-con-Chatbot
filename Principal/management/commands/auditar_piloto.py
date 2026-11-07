"""Auditoría ejecutable de puesta en marcha sin mostrar datos personales.

Uso:
  python manage.py auditar_piloto
  python manage.py auditar_piloto --ollama --modelo --estricto
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from Principal.models import (
    Estudiante, IntentoEvaluacion, Matricula, PreguntaBanco,
)
from Principal.management.commands.auditar_cierre import comprobar_ollama


class Command(BaseCommand):
    help = "Revisar requisitos del piloto sin modificar estudiantes ni modelos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ollama", action="store_true",
            help="Probar Ollama local con una pregunta sintética."
        )
        parser.add_argument(
            "--modelo", action="store_true",
            help="Evaluar suficiencia estadística sin entrenar."
        )
        parser.add_argument(
            "--estricto", action="store_true",
            help="Retornar error si faltan requisitos mínimos de operación."
        )

    def handle(self, *args, **options):
        errores = []
        advertencias = []
        es_prod = settings.ENVIRONMENT == "production"

        if not es_prod:
            errores.append("No está configurado DJANGO_ENV=production.")
        if settings.DEBUG:
            errores.append("DEBUG debe estar desactivado.")
        motor = settings.DATABASES["default"]["ENGINE"]
        if "postgresql" not in motor:
            errores.append("El servidor necesita PostgreSQL persistente.")
        if not settings.DATA_ROOT:
            errores.append("Falta DJANGO_DATA_ROOT para archivos y memorias.")
        else:
            raiz = settings.DATA_ROOT
            if not raiz.is_dir():
                errores.append("La ruta persistente no está montada en el servidor.")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                errores.append("Hay migraciones pendientes.")
        except Exception:
            errores.append("No se pudo validar la conexión o migraciones de la BD.")

        registrados = Estudiante.objects.count()
        matriculas = Matricula.objects.filter(activa=True).count()
        evaluaciones = IntentoEvaluacion.objects.count()
        preguntas = PreguntaBanco.objects.filter(
            estado="APROBADA", activo=True,
        ).count()
        if preguntas < 30:
            advertencias.append(
                "Banco aprobado pequeño: no interpretar esto como equivalente al Saber 11."
            )
        if registrados == 0 or matriculas == 0:
            advertencias.append("No hay estudiantes o matrículas activos para piloto.")
        advertencias.extend([
            "No se habilita multiinstitución: falta aislamiento extremo a extremo.",
            "Faltan pruebas humanas con audio real, documentos de ejemplo y accesibilidad.",
            "La adecuación legal y los respaldos/restauraciones requieren verificación externa.",
        ])

        resultado = {
            "entorno": settings.ENVIRONMENT,
            "motor": motor,
            "estudiantes": registrados,
            "matriculas_activas": matriculas,
            "evaluaciones": evaluaciones,
            "preguntas_aprobadas": preguntas,
            "ollama": (
                comprobar_ollama() if options["ollama"]
                else {"estado": "no_comprobado"}
            ),
            "errores": errores,
            "advertencias": advertencias,
        }
        if options["modelo"]:
            from Principal.services.prediccion_academica import auditar_datos

            auditoria = auditar_datos()
            resultado["prediccion"] = {
                "estudiantes_elegibles": auditoria["estudiantes"],
                "ejemplos": auditoria["ejemplos"],
                "suficiente_para_intentar": auditoria["suficiente_para_intentar"],
            }
        self.stdout.write(json.dumps(resultado, ensure_ascii=False, indent=2))
        if options["estricto"] and (
            errores or (options["ollama"] and resultado["ollama"]["estado"] != "correcto")
        ):
            raise CommandError("La instalación no supera la auditoría mínima de piloto.")
