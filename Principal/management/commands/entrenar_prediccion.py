"""Audita datos históricos y entrena una predicción si supera validaciones.

Ejemplos:
  python manage.py entrenar_prediccion
  python manage.py entrenar_prediccion --entrenar

Nunca se generan datos sintéticos ni se mezclan cuentas demo.
El modelo se guarda como parámetros JSON privados, sin IDs ni respuestas.
"""
import json

from django.core.management.base import BaseCommand, CommandError

from Principal.services.prediccion_academica import (
    auditar_datos, entrenar_y_evaluar,
)


class Command(BaseCommand):
    help = (
        "Auditar suficiencia de evaluaciones y opcionalmente entrenar/validar "
        "un clasificador de riesgo en el siguiente intento."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--entrenar", action="store_true",
            help="Entrenar, evaluar en estudiantes separados y publicar solo si aprueba.",
        )

    def handle(self, *args, **options):
        if not options["entrenar"]:
            datos = auditar_datos()
            self.stdout.write(json.dumps(datos, ensure_ascii=False, indent=2))
            if not datos["suficiente_para_intentar"]:
                self.stdout.write(self.style.WARNING(
                    "No hay datos suficientes: no se ha entrenado ni publicado ningún modelo."
                ))
            else:
                self.stdout.write("Datos mínimos presentes. Ejecuta --entrenar para evaluar.")
            return

        resultado = entrenar_y_evaluar()
        self.stdout.write(json.dumps(resultado, ensure_ascii=False, indent=2))
        if not resultado["publicado"]:
            raise CommandError(
                "La predicción no se publicó: " + resultado["motivo"]
            )
        self.stdout.write(self.style.SUCCESS(
            "Modelo validado guardado en .local-data/prediccion/modelo.json"
        ))
