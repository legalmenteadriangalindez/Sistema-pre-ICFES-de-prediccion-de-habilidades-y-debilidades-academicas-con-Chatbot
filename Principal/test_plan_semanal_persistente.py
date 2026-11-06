"""Pruebas de persistencia, métricas y aislamiento de planes de estudio."""
import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import (
    Acudiente, Estudiante, EstudianteAcudiente, IntentoEvaluacion,
    Persona, PlanEstudioSemanal, PerfilUsuario, RelacionAcudiente, RespuestaEvaluacion,
    Rol, SesionPlanSemanal, Sexo,
)
from .services.plan_persistente import (
    crear_plan_actual, historial_semanal, lunes_de, resumen_plan,
)


HOY = date(2026, 11, 6)
LUNES = date(2026, 11, 2)


@patch("Principal.portal_academico.timezone.localdate", return_value=HOY)
class PlanSemanalPersistenteTests(TestCase):
    def setUp(self):
        sexo = Sexo.objects.create(descripcion="Prueba seguimiento")
        self.usuario = User.objects.create_user(
            username="alumno_semanal", password="Segura!2026"
        )
        self.perfil = PerfilUsuario.objects.create(user=self.usuario)
        self.perfil.roles.add(Rol.objects.create(nombre="ESTUDIANTE"))
        persona = Persona.objects.create(
            perfil_user=self.perfil, nombre="Ana", apellido="Seguimiento",
            documento="PLAN-EST-01", fecha_nacimiento=date(2008, 1, 1),
            direccion="Calle simulada", telefono="3000000000", sexo=sexo,
        )
        self.estudiante = Estudiante.objects.create(persona=persona)
        self.otro_usuario = User.objects.create_user(
            username="otro_semanal", password="Segura!2026"
        )
        otro_perfil = PerfilUsuario.objects.create(user=self.otro_usuario)
        otra_persona = Persona.objects.create(
            perfil_user=otro_perfil, nombre="Otro", apellido="Alumno",
            documento="PLAN-EST-02", fecha_nacimiento=date(2008, 1, 1),
            direccion="Otra dirección", telefono="3000000001", sexo=sexo,
        )
        self.otro = Estudiante.objects.create(persona=otra_persona)
        self.url = reverse("plan_semanal")
        self.client.force_login(self.usuario)

    def _crear(self):
        r = self.client.post(self.url, {"accion": "crear"})
        self.assertRedirects(r, self.url)
        return PlanEstudioSemanal.objects.get(estudiante=self.estudiante)

    def test_get_ofrece_propuesta_sin_crear_registros(self, hoy_mock):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Crear y guardar mi plan")
        self.assertEqual(len(respuesta.context["propuesta"]), 7)
        self.assertFalse(PlanEstudioSemanal.objects.exists())
        self.assertFalse(SesionPlanSemanal.objects.exists())

    def test_creacion_persiste_siete_dias_con_lunes_y_domingo(self, hoy_mock):
        plan = self._crear()
        self.assertEqual(plan.semana_inicio, LUNES)
        self.assertFalse(plan.con_datos_academicos)
        sesiones = list(plan.sesiones.all())
        self.assertEqual(len(sesiones), 7)
        self.assertEqual([x.dia_indice for x in sesiones], list(range(7)))
        self.assertEqual(sesiones[0].fecha_programada, LUNES)
        self.assertEqual(sesiones[-1].fecha_programada, LUNES + timedelta(days=6))
        self.assertEqual(resumen_plan(plan)["minutos_objetivo"], 215)
        self.assertEqual(self.client.get(self.url).context["progreso"]["porcentaje"], 0)

    def test_generacion_repetida_no_duplicada_ni_reinicia_avances(self, hoy_mock):
        plan = self._crear()
        sesion = plan.sesiones.first()
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesion.pk, "minutos": "42",
            "notas": "Repasé álgebra",
        })
        respuesta = self.client.post(self.url, {"accion": "crear"})
        self.assertRedirects(respuesta, self.url)
        self.assertEqual(PlanEstudioSemanal.objects.count(), 1)
        self.assertEqual(SesionPlanSemanal.objects.count(), 7)
        sesion.refresh_from_db()
        self.assertTrue(sesion.completada)
        self.assertEqual(sesion.minutos_realizados, 42)
        self.assertEqual(sesion.notas, "Repasé álgebra")

    def test_registro_actualiza_metricas_y_admite_edicion(self, hoy_mock):
        plan = self._crear()
        sesiones = list(plan.sesiones.all())
        for s in sesiones[:2]:
            respuesta = self.client.post(self.url, {
                "accion": "registrar", "sesion_id": s.pk, "minutos": "30",
            })
            self.assertRedirects(respuesta, self.url)
        progreso = self.client.get(self.url).context["progreso"]
        self.assertEqual(progreso["completadas"], 2)
        self.assertEqual(progreso["pendientes"], 5)
        self.assertEqual(progreso["porcentaje"], 29)
        self.assertEqual(progreso["minutos_realizados"], 60)
        self.assertEqual(progreso["minutos_objetivo"], 215)
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesiones[0].pk,
            "minutos": "45", "notas": "Terminé los problemas",
        })
        actualizado = resumen_plan(plan)
        self.assertEqual(actualizado["completadas"], 2)
        self.assertEqual(actualizado["minutos_realizados"], 75)

    def test_reabrir_corrige_registro_sin_eliminar_sesion(self, hoy_mock):
        plan = self._crear()
        sesion = plan.sesiones.first()
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesion.pk,
            "minutos": "35", "notas": "Práctica",
        })
        self.assertRedirects(
            self.client.post(self.url, {
                "accion": "reabrir", "sesion_id": sesion.pk
            }), self.url,
        )
        sesion.refresh_from_db()
        self.assertFalse(sesion.completada)
        self.assertEqual(sesion.minutos_realizados, 0)
        self.assertIsNone(sesion.fecha_completada)
        self.assertEqual(sesion.notas, "")
        self.assertEqual(plan.sesiones.count(), 7)

    def test_rechaza_minutos_invalidos_y_notas_extensas(self, hoy_mock):
        plan = self._crear()
        sesion = plan.sesiones.first()
        for valor in ("0", "-3", "481", "no-es-numero", ""):
            with self.subTest(minutos=valor):
                self.client.post(self.url, {
                    "accion": "registrar", "sesion_id": sesion.pk,
                    "minutos": valor,
                })
                sesion.refresh_from_db()
                self.assertFalse(sesion.completada)
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesion.pk,
            "minutos": "30", "notas": "a" * 501,
        })
        sesion.refresh_from_db()
        self.assertFalse(sesion.completada)
        self.assertEqual(sesion.minutos_realizados, 0)

    def test_no_permite_modificar_sesiones_de_otro_estudiante(self, hoy_mock):
        plan_otro, creado = crear_plan_actual(self.otro, LUNES)
        self.assertTrue(creado)
        sesion_ajena = plan_otro.sesiones.first()
        for accion in ("registrar", "reabrir"):
            with self.subTest(accion=accion):
                respuesta = self.client.post(self.url, {
                    "accion": accion, "sesion_id": sesion_ajena.pk,
                    "minutos": "60",
                })
                self.assertEqual(respuesta.status_code, 404)
        sesion_ajena.refresh_from_db()
        self.assertFalse(sesion_ajena.completada)
        self.assertEqual(len(self.client.get(self.url).context["historial"]), 0)

    def test_historico_es_solo_lectura_y_no_se_puede_reabrir_por_post(self, hoy_mock):
        anterior = LUNES - timedelta(days=7)
        viejo, _ = crear_plan_actual(self.estudiante, anterior)
        sesion = viejo.sesiones.first()
        respuesta = self.client.get(self.url + f"?semana={anterior.isoformat()}")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context["es_semana_actual"])
        self.assertContains(respuesta, "solo lectura")
        self.assertEqual(self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesion.pk, "minutos": "33",
        }).status_code, 404)
        sesion.refresh_from_db()
        self.assertFalse(sesion.completada)

    def test_historial_conserva_semanas_y_porcentajes(self, hoy_mock):
        anterior = LUNES - timedelta(days=7)
        viejo, _ = crear_plan_actual(self.estudiante, anterior)
        sesion = viejo.sesiones.first()
        sesion.completada = True
        sesion.minutos_realizados = 20
        sesion.save(update_fields=["completada", "minutos_realizados"])
        actual = self._crear()
        historial = historial_semanal(self.estudiante)
        self.assertEqual(len(historial), 2)
        self.assertEqual([x["plan"].pk for x in historial], [actual.pk, viejo.pk])
        self.assertEqual(historial[0]["progreso"]["porcentaje"], 0)
        self.assertEqual(historial[1]["progreso"]["porcentaje"], 14)

    def test_nuevas_evaluaciones_no_reescriben_plan_ya_guardado(self, hoy_mock):
        plan = self._crear()
        detalle_original = [(x.pk, x.area, x.actividad) for x in plan.sesiones.all()]
        intento = IntentoEvaluacion.objects.create(
            estudiante=self.estudiante, materia="Matemáticas",
            total_preguntas=4, aciertos=0,
        )
        for numero in range(4):
            RespuestaEvaluacion.objects.create(
                intento=intento, numero=numero, competencia="Álgebra",
                enunciado="", pregunta=f"Pregunta {numero}",
                opciones={"A": "Sí", "B": "No"},
                respuesta_estudiante="A", respuesta_correcta="B",
                explicacion="", es_correcta=False,
            )
        self.client.post(self.url, {"accion": "crear"})
        plan.refresh_from_db()
        self.assertFalse(plan.con_datos_academicos)
        self.assertEqual(
            [(x.pk, x.area, x.actividad) for x in plan.sesiones.all()],
            detalle_original,
        )

    def test_exportacion_incluye_solo_planes_y_notas_propias(self, hoy_mock):
        plan = self._crear()
        sesion = plan.sesiones.first()
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": sesion.pk,
            "minutos": "29", "notas": "Mi actividad privada",
        })
        otro_plan, _ = crear_plan_actual(self.otro, LUNES)
        otra_sesion = otro_plan.sesiones.first()
        otra_sesion.notas = "Información secreta de otra cuenta"
        otra_sesion.save(update_fields=["notas"])
        datos = json.loads(self.client.get(reverse("exportar_mis_datos")).content)
        planes = datos["estudiante"]["planes_semanales"]
        self.assertEqual(len(planes), 1)
        self.assertEqual(len(planes[0]["sesiones"]), 7)
        self.assertIn("Mi actividad privada", json.dumps(datos, ensure_ascii=False))
        self.assertNotIn("Información secreta", json.dumps(datos, ensure_ascii=False))

    def test_sin_perfil_no_puede_crear_planes(self, hoy_mock):
        usuario_sin_perfil = User.objects.create_user(
            username="cuenta_sin_estudiante", password="Segura!2026"
        )
        self.client.force_login(usuario_sin_perfil)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {"accion": "crear"}).status_code, 403)

    def test_metodos_y_fechas_invalidas(self, hoy_mock):
        self.assertEqual(self.client.put(self.url, data="incorrecto").status_code, 405)
        self.assertEqual(self.client.get(self.url + "?semana=invalida").status_code, 400)
        self.assertEqual(self.client.get(self.url + "?semana=2026-11-03").status_code, 400)
        self.assertEqual(self.client.post(self.url, {"accion": "desconocida"}).status_code, 400)

    def test_acudiente_ve_progreso_solo_de_estudiante_vinculado(self, hoy_mock):
        plan = self._crear()
        s = plan.sesiones.first()
        self.client.post(self.url, {
            "accion": "registrar", "sesion_id": s.pk, "minutos": "40",
        })
        crear_plan_actual(self.otro, LUNES)
        acudiente_user = User.objects.create_user(
            username="acudiente_semanal", password="Segura!2026"
        )
        perfil_acu = PerfilUsuario.objects.create(user=acudiente_user)
        perfil_acu.roles.add(Rol.objects.create(nombre="ACUDIENTE"))
        persona_acu = Persona.objects.create(
            perfil_user=perfil_acu, nombre="Padre", apellido="De prueba",
            documento="PLAN-ACU-01", fecha_nacimiento=date(1978, 1, 1),
            direccion="Calle simulada", telefono="3000000002",
            sexo=Sexo.objects.first(),
        )
        acudiente = Acudiente.objects.create(persona=persona_acu)
        relacion = RelacionAcudiente.objects.create(descripcion="Responsable")
        EstudianteAcudiente.objects.create(
            acudiente=acudiente, estudiante=self.estudiante, relacion=relacion,
        )
        self.client.force_login(acudiente_user)
        response = self.client.get(reverse("acudiente"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["hijos"]), 1)
        self.assertEqual(response.context["hijos"][0]["plan_semanal"]["completadas"], 1)
        self.assertEqual(response.context["hijos"][0]["plan_semanal"]["minutos_realizados"], 40)
        self.assertNotContains(response, "Otro Alumno")
        self.assertEqual(self.client.post(self.url, {"accion": "crear"}).status_code, 403)

    def test_csrf_impide_crear_plan_sin_token(self, hoy_mock):
        otro_cliente = Client(enforce_csrf_checks=True)
        otro_cliente.force_login(self.usuario)
        respuesta = otro_cliente.post(self.url, {"accion": "crear"})
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(PlanEstudioSemanal.objects.exists())
