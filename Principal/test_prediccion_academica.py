"""Pruebas de predicción: datos reales de Django y sintéticos SOLO en memoria de test.

Nunca genera cuentas ni resultados de entrenamiento en la base del usuario.
"""
import json
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Estudiante, IntentoEvaluacion, PerfilUsuario, Persona,
    RespuestaEvaluacion, Rol, Sexo,
)
from .services.prediccion_academica import (
    AREAS_BASE, CARACTERISTICAS, VERSION, _area, _vector,
    auditar_datos, cargar_modelo, construir_muestras, entrenar_y_evaluar,
    extraer_eventos, predicciones_estudiante,
)


class PrediccionBasesTests(TestCase):
    def setUp(self):
        self.archivos = tempfile.TemporaryDirectory()
        self.addCleanup(self.archivos.cleanup)
        self.ruta = Path(self.archivos.name) / "modelo.json"
        self.ajustes = override_settings(PREDICCION_MODELO_PATH=self.ruta)
        self.ajustes.enable()
        self.addCleanup(self.ajustes.disable)

    def test_sin_datos_no_entrena_ni_guarda_archivo(self):
        datos = auditar_datos()
        self.assertEqual(datos["ejemplos"], 0)
        self.assertFalse(datos["suficiente_para_intentar"])
        resultado = entrenar_y_evaluar()
        self.assertFalse(resultado["publicado"])
        self.assertIsNone(cargar_modelo())
        self.assertFalse(self.ruta.exists())

    def test_integral_toma_area_de_competencia(self):
        self.assertEqual(_area("Simulacro: Integral ampliado", "Matemáticas · Álgebra"), "Matemáticas")
        self.assertEqual(_area("Simulacro: Integral", "Inglés · Lectura"), "Inglés")
        self.assertIsNone(_area("Simulacro: Integral", "Etiqueta inventada"))
        self.assertEqual(_area("Simulacro: Ciencias Naturales", "Biología"), "Ciencias Naturales")

    def test_la_muestra_solo_usa_pasado_para_predecir_proxima_evaluacion(self):
        fecha = datetime(2026, 1, 1, tzinfo=timezone.utc)
        eventos = [
            {"fecha": fecha + timedelta(days=i), "intento_id": i,
             "total": 10, "aciertos": n}
            for i, n in enumerate([8, 7, 2, 9], start=1)
        ]
        historias = {4: {"Matemáticas": eventos}}
        x, y, grupos = construir_muestras(historias)
        self.assertEqual(len(x), 2)
        self.assertEqual(y, [1, 0])
        self.assertEqual(grupos, [4, 4])
        self.assertAlmostEqual(x[0][0], 0.7)
        self.assertAlmostEqual(x[0][1], 0.75)
        self.assertEqual(x[0], _vector(eventos[:2], "Matemáticas"))
        # Cambiar la nota futura no cambia las características disponibles antes.
        eventos[2]["aciertos"] = 10
        segundo_x, segundo_y, _ = construir_muestras(historias)
        self.assertEqual(segundo_x[0], x[0])
        self.assertEqual(segundo_y[0], 0)
        self.assertNotEqual(segundo_x[1], x[1])

    def test_rechaza_json_incompatible_o_malicioso_sin_deserializar_pickle(self):
        self.ruta.write_text('{"version":"distinta"}', encoding="utf-8")
        self.assertIsNone(cargar_modelo())
        self.ruta.write_text("__import__('os').system('echo nunca')", encoding="utf-8")
        self.assertIsNone(cargar_modelo())

    def test_comando_solo_audita_sin_publicar_modelo(self):
        from io import StringIO
        salida = StringIO()
        call_command("entrenar_prediccion", stdout=salida)
        self.assertIn('"ejemplos": 0', salida.getvalue())
        self.assertFalse(self.ruta.exists())
        with self.assertRaises(CommandError):
            call_command("entrenar_prediccion", "--entrenar", stdout=StringIO())

    def test_no_publica_si_todos_los_resultados_pertenecen_a_una_clase(self):
        fecha = datetime(2026, 1, 1, tzinfo=timezone.utc)
        historias = {
            idx: {"Matemáticas": [
                {"fecha": fecha + timedelta(days=j), "intento_id": j,
                 "total": 10, "aciertos": 2}
                for j in range(6)
            ]}
            for idx in range(75)
        }
        auditoria = auditar_datos(historias)
        self.assertGreaterEqual(auditoria["ejemplos"], 150)
        self.assertFalse(auditoria["condiciones"]["casos_sin_riesgo"])


class VistasPrediccionTests(TestCase):
    def setUp(self):
        self.archivos = tempfile.TemporaryDirectory()
        self.addCleanup(self.archivos.cleanup)
        self.ruta = Path(self.archivos.name) / "modelo.json"
        self.settings = override_settings(PREDICCION_MODELO_PATH=self.ruta)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.alumno = User.objects.create_user(
            "student_predictions", password="ClaveSegura!2026"
        )
        self.admin = User.objects.create_superuser(
            "admin_predictions", "admin@ejemplo.test", "ClaveSegura!2026"
        )
        self.ajeno = User.objects.create_user(
            "other_predictions", password="ClaveSegura!2026"
        )
        sexo = Sexo.objects.create(descripcion="Test")
        perfil = PerfilUsuario.objects.create(user=self.alumno)
        perfil.roles.add(Rol.objects.create(nombre="ESTUDIANTE"))
        persona = Persona.objects.create(
            perfil_user=perfil, nombre="Alumno", apellido="Test",
            documento="PRED-001", fecha_nacimiento=date(2008, 1, 1),
            direccion="Prueba", telefono="3000000000", sexo=sexo,
        )
        self.estudiante = Estudiante.objects.create(persona=persona)

    def test_estudiante_ve_estado_no_validado_sin_inventar_probabilidades(self):
        self.client.force_login(self.alumno)
        respuesta = self.client.get(reverse("prediccion_estudiante"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["sin_modelo"])
        self.assertContains(respuesta, "Predicción aún no validada")
        self.assertEqual(respuesta.context["predicciones"], [])

    def test_admin_ve_suficiencia_y_alumno_no_accede_al_panel(self):
        url = reverse("validacion_prediccion")
        self.client.force_login(self.alumno)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["auditoria_actual"]["suficiente_para_intentar"])
        self.assertContains(response, "Datos insuficientes")

    def test_sin_perfil_estudiante_no_puede_consultar_prediccion_ajena(self):
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(reverse("prediccion_estudiante")).status_code, 403)

    def test_rutas_no_aceptan_post(self):
        self.client.force_login(self.alumno)
        self.assertEqual(self.client.post(reverse("prediccion_estudiante")).status_code, 405)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse("validacion_prediccion")).status_code, 405)

    def test_artifact_modelo_de_prueba_muestra_una_alerta_sin_datos_de_otros(self):
        from django.utils import timezone as django_timezone
        ahora = django_timezone.now()
        pruebas = []
        for i in range(2):
            intento = IntentoEvaluacion.objects.create(
                estudiante=self.estudiante, materia="Matemáticas",
                total_preguntas=10, aciertos=2
            )
            # Distintos tiempos para preservar el orden del historial.
            IntentoEvaluacion.objects.filter(pk=intento.pk).update(
                fecha=ahora - timedelta(days=4 - i)
            )
            pruebas.extend([
                RespuestaEvaluacion(
                    intento=intento, numero=n, competencia="Álgebra",
                    enunciado="", pregunta=f"Ejercicio {n}",
                    opciones={"A": "Sí", "B": "No"},
                    respuesta_estudiante="A", respuesta_correcta="B",
                    explicacion="", es_correcta=n < 2,
                ) for n in range(10)
            ])
        RespuestaEvaluacion.objects.bulk_create(pruebas)
        self.ruta.write_text(json.dumps({
            "version": VERSION,
            "caracteristicas": list(CARACTERISTICAS),
            "entrenado_en": ahora.isoformat(),
            "media": [0] * len(CARACTERISTICAS),
            "escala": [1] * len(CARACTERISTICAS),
            "coeficientes": [0] * len(CARACTERISTICAS),
            "intercepto": 2,
            "umbral_alerta": 0.5,
            "evaluacion": {},
        }), encoding="utf-8")
        self.client.force_login(self.alumno)
        response = self.client.get(reverse("prediccion_estudiante"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["predicciones"]), 1)
        self.assertEqual(response.context["predicciones"][0]["area"], "Matemáticas")
        self.assertTrue(response.context["predicciones"][0]["alerta"])
        self.assertContains(response, "Priorizar práctica")


class EntrenamientoEvaluadoTests(TestCase):
    """Datos simulados de test para ejercitar el algoritmo, NUNCA para producción."""

    def setUp(self):
        self.archivos = tempfile.TemporaryDirectory()
        self.addCleanup(self.archivos.cleanup)
        self.ruta = Path(self.archivos.name) / "ml" / "modelo.json"
        self.ajustes = override_settings(PREDICCION_MODELO_PATH=self.ruta)
        self.ajustes.enable()
        self.addCleanup(self.ajustes.disable)

    def test_entrenamiento_requiere_mejora_y_valida_alumnos_independientes(self):
        sexo = Sexo.objects.create(descripcion="Simulado-test")
        respuestas = []
        for numero in range(80):
            usuario = User.objects.create(username=f"synthetic_ml_{numero:03d}")
            perfil = PerfilUsuario.objects.create(user=usuario)
            persona = Persona.objects.create(
                perfil_user=perfil, nombre="Ficticio", apellido="Test",
                documento=f"SYN-ML-{numero:03d}",
                fecha_nacimiento=date(2008, 1, 1), direccion="Sintético",
                telefono="0000000000", sexo=sexo,
            )
            alumno = Estudiante.objects.create(persona=persona)
            puntaje = 2 if numero % 2 else 9
            for evento in range(5):
                intento = IntentoEvaluacion.objects.create(
                    estudiante=alumno, materia="Matemáticas",
                    total_preguntas=10, aciertos=puntaje,
                )
                # El valor correcto de una respuesta siempre viene del
                # proceso de calificación, no de datos futuros.
                respuestas.extend([
                    RespuestaEvaluacion(
                        intento=intento, numero=pregunta,
                        competencia="Álgebra", enunciado="",
                        pregunta=f"Sintética {pregunta}",
                        opciones={"A": "uno", "B": "dos"},
                        respuesta_estudiante="A",
                        respuesta_correcta=("A" if pregunta < puntaje else "B"),
                        explicacion="Solo test",
                        es_correcta=pregunta < puntaje,
                    )
                    for pregunta in range(10)
                ])
        RespuestaEvaluacion.objects.bulk_create(respuestas, batch_size=500)

        audit = auditar_datos()
        self.assertTrue(audit["suficiente_para_intentar"])
        self.assertEqual(audit["estudiantes"], 80)
        self.assertEqual(audit["ejemplos"], 240)
        self.assertEqual(audit["casos_riesgo"], 120)
        self.assertEqual(audit["casos_sin_riesgo"], 120)

        resultado = entrenar_y_evaluar()
        self.assertTrue(resultado["publicado"], resultado["motivo"])
        evaluacion = resultado["evaluacion"]
        self.assertGreaterEqual(evaluacion["prueba_estudiantes"], 8)
        self.assertEqual(
            evaluacion["prueba_estudiantes"] + evaluacion["entrenamiento_estudiantes"], 80
        )
        self.assertGreaterEqual(evaluacion["metricas"]["exactitud_balanceada"], 0.8)
        self.assertGreaterEqual(evaluacion["metricas"]["precision_riesgo"], 0.8)
        self.assertGreaterEqual(evaluacion["metricas"]["recuperacion_riesgo"], 0.8)
        self.assertTrue(self.ruta.is_file())

        guardado = cargar_modelo()
        self.assertEqual(guardado["version"], VERSION)
        self.assertEqual(len(guardado["coeficientes"]), len(CARACTERISTICAS))
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertNotIn("synthetic_ml_", texto)
        self.assertNotIn("SYN-ML-", texto)
        uno = Estudiante.objects.get(persona__perfil_user__user__username="synthetic_ml_001")
        predicho = predicciones_estudiante(uno)
        self.assertEqual(len(predicho), 1)
        self.assertEqual(predicho[0]["area"], "Matemáticas")
        self.assertTrue(predicho[0]["alerta"])
