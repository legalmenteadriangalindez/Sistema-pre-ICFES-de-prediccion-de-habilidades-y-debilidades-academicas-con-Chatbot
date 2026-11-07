"""Pruebas integrales con datos ficticios de las cuatro prioridades."""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Principal.models import (
    AnioLectivo, AsignacionDocenteCurso, Curso, Estudiante, Grado,
    IntentoEvaluacion, IntervencionAcademica, Matricula, PerfilUsuario,
    Persona, PreguntaBanco, RespuestaEvaluacion, Rol, Sexo, SimulacroAvanzado,
)
from Principal.services.calidad_preguntas import analizar_pregunta, consistencia_por_formulario


class PrioridadesAltasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            "admin_altas", "admin-altas@example.test", "Clave!2026",
        )
        cls.docente = User.objects.create_user("doc_altas", password="Clave!2026")
        cls.revisor = User.objects.create_user("revisor_altas", password="Clave!2026")
        cls.ajeno = User.objects.create_user("doc_sin_permiso_altas", password="Clave!2026")
        cls.usuarios = [
            User.objects.create_user(f"alumno_altas_{i}", password="Clave!2026")
            for i in range(2)
        ]
        docente_rol, _ = Rol.objects.get_or_create(nombre="DOCENTE")
        estudiante_rol, _ = Rol.objects.get_or_create(nombre="ESTUDIANTE")
        for usuario in (cls.docente, cls.revisor, cls.ajeno):
            perfil = PerfilUsuario.objects.create(user=usuario)
            perfil.roles.add(docente_rol)
        cls.sexo = Sexo.objects.create(descripcion="Prueba de cierre")
        cls.estudiantes = []
        for i, usuario in enumerate(cls.usuarios):
            perfil = PerfilUsuario.objects.create(user=usuario)
            perfil.roles.add(estudiante_rol)
            persona = Persona.objects.create(
                perfil_user=perfil, nombre=f"Prueba{i}", apellido="Cierre",
                documento=f"CIE-ALTAS-{i}", fecha_nacimiento=date(2008, 1, 1),
                direccion="Prueba", telefono="0000000", sexo=cls.sexo,
            )
            cls.estudiantes.append(Estudiante.objects.create(persona=persona))
        grado = Grado.objects.create(nombre="Once cierres")
        curso = Curso.objects.create(grado=grado, nombre="A")
        anio = AnioLectivo.objects.create(
            anio=2026, fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31), activo=True,
        )
        cls.matricula = Matricula.objects.create(
            estudiante=cls.estudiantes[0], curso=curso, anio_lectivo=anio,
        )
        Matricula.objects.create(
            estudiante=cls.estudiantes[1], curso=curso, anio_lectivo=anio,
        )
        for usuario in (cls.docente, cls.revisor):
            AsignacionDocenteCurso.objects.create(
                docente=usuario.perfilusuario, curso=curso, anio_lectivo=anio,
            )

    def pregunta(self):
        return PreguntaBanco.objects.create(
            materia="Matemáticas", competencia="Sumas", evidencia="Resolver",
            enunciado="¿Cuánto vale dos más dos?",
            opciones={"A": "Tres", "B": "Cuatro", "C": "Cinco", "D": "Seis"},
            respuesta_correcta="B", explicacion="La suma es cuatro.",
            estado="APROBADA", creado_por=self.docente, revisado_por=self.revisor,
        )

    def agregar_respuestas(self, estudiante, correctas, competencia="Sumas"):
        intento = IntentoEvaluacion.objects.create(
            estudiante=estudiante, materia="Matemáticas",
            total_preguntas=len(correctas), aciertos=sum(correctas),
        )
        for n, correcta in enumerate(correctas):
            RespuestaEvaluacion.objects.create(
                intento=intento, numero=n, competencia=competencia,
                enunciado="", pregunta="Operación de práctica",
                opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
                respuesta_estudiante="B" if correcta else "A",
                respuesta_correcta="B", explicacion="Verificar",
                es_correcta=correcta,
            )
        return intento

    def test_simulacro_autoguardado_pausa_recarga_y_bloqueo_de_otros_bloques(self):
        self.client.force_login(self.usuarios[0])
        url = reverse("simulacro_avanzado")
        self.assertEqual(self.client.post(url, {"accion": "iniciar"}).status_code, 302)
        examen = SimulacroAvanzado.objects.get(estudiante=self.estudiantes[0])
        self.assertEqual(len(examen.preguntas), 50)
        self.assertEqual(examen.bloque, 1)
        respuesta = self.client.post(url, {
            "accion": "guardar", "indice": "0", "valor": examen.preguntas[0]["correcta"],
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["ok"])
        self.assertEqual(self.client.post(url, {
            "accion": "guardar", "indice": "25", "valor": "A",
        }).status_code, 400)
        self.assertEqual(self.client.post(url, {"accion": "pausar"}).status_code, 302)
        recargada = self.client.get(url)
        self.assertContains(recargada, "Reanudar bloque 1")
        self.assertEqual(self.client.post(url, {"accion": "reanudar"}).status_code, 302)
        recargada = self.client.get(url)
        self.assertContains(recargada, "Las respuestas se guardan automáticamente")
        self.assertNotContains(recargada, examen.preguntas[0]["explicacion"])
        examen.refresh_from_db()
        self.assertIn("0", examen.respuestas)
        self.assertEqual(SimulacroAvanzado.objects.count(), 1)
        self.assertEqual(self.client.post(url, {"accion": "iniciar"}).status_code, 302)
        self.assertEqual(SimulacroAvanzado.objects.count(), 1)

    def test_simulacro_limite_tiempo_finalizacion_idempotente_y_acceso_ajeno(self):
        self.client.force_login(self.usuarios[0])
        url = reverse("simulacro_avanzado")
        self.client.post(url, {"accion": "iniciar"})
        examen = SimulacroAvanzado.objects.get(estudiante=self.estudiantes[0])
        examen.vence_en = timezone.now() - timedelta(minutes=1)
        examen.save(update_fields=["vence_en"])
        self.assertEqual(self.client.post(url, {
            "accion": "guardar", "indice": "0", "valor": "A",
        }).status_code, 400)
        self.assertEqual(self.client.post(url, {"accion": "reanudar"}).status_code, 200)
        self.assertEqual(self.client.post(url, {"accion": "siguiente_bloque"}).status_code, 302)
        examen.refresh_from_db()
        self.assertEqual(examen.bloque, 2)
        self.assertEqual(self.client.post(url, {"accion": "reanudar"}).status_code, 302)
        self.assertEqual(self.client.post(url, {
            "accion": "guardar", "indice": "25", "valor": "A",
        }).status_code, 200)
        self.assertEqual(self.client.post(url, {"accion": "finalizar"}).status_code, 302)
        self.assertEqual(self.client.post(url, {"accion": "finalizar"}).status_code, 200)
        examen.refresh_from_db()
        self.assertEqual(examen.estado, "FINALIZADO")
        self.assertEqual(IntentoEvaluacion.objects.count(), 1)
        self.assertEqual(RespuestaEvaluacion.objects.filter(
            intento=examen.intento,
        ).count(), 50)
        ver = reverse("resultado_simulacro_avanzado", args=[examen.pk])
        self.assertEqual(self.client.get(ver).status_code, 200)
        self.client.force_login(self.usuarios[1])
        self.assertEqual(self.client.get(ver).status_code, 404)
        self.assertEqual(self.client.get(url).context["examen"], None)

    def test_versionado_otra_revision_y_trazabilidad_de_respuesta(self):
        raiz = self.pregunta()
        intento = self.agregar_respuestas(self.estudiantes[0], [True, False])
        respuesta = RespuestaEvaluacion.objects.filter(intento=intento).first()
        respuesta.pregunta_banco = raiz
        respuesta.save(update_fields=["pregunta_banco"])
        self.client.force_login(self.docente)
        url = reverse("crear_revision_banco", args=[raiz.pk])
        crear = self.client.post(url)
        self.assertEqual(crear.status_code, 302)
        revision = PreguntaBanco.objects.get(revision_de=raiz)
        self.assertEqual(revision.numero_version, 2)
        self.assertEqual(revision.enunciado, raiz.enunciado)
        self.assertEqual(revision.estado, "BORRADOR")
        self.assertNotEqual(revision.huella, raiz.huella)
        self.assertEqual(self.client.post(
            reverse("enviar_pregunta_revision", args=[revision.pk]),
        ).status_code, 302)
        self.assertEqual(self.client.post(
            reverse("revisar_pregunta_banco", args=[revision.pk]),
            {"accion": "aprobar"},
        ).status_code, 403)
        self.client.force_login(self.revisor)
        self.assertEqual(self.client.post(
            reverse("revisar_pregunta_banco", args=[revision.pk]),
            {"accion": "aprobar", "observacion": "Corrección validada"},
        ).status_code, 302)
        raiz.refresh_from_db()
        revision.refresh_from_db()
        self.assertFalse(raiz.activo)
        self.assertTrue(revision.activo)
        self.assertEqual(revision.estado, "APROBADA")
        respuesta.refresh_from_db()
        self.assertEqual(respuesta.pregunta_banco_id, raiz.pk)
        self.assertEqual(self.client.get(
            reverse("historial_versiones_banco", args=[raiz.pk])
        ).status_code, 200)

    def test_calidad_sin_datos_no_inventa_dificultad_ni_discriminacion(self):
        pregunta = self.pregunta()
        resumen = analizar_pregunta(pregunta)
        self.assertEqual(resumen["n"], 0)
        self.assertIsNone(resumen["dificultad"])
        self.assertIsNone(resumen["discriminacion"])
        self.assertEqual(consistencia_por_formulario(), [])
        self.client.force_login(self.usuarios[0])
        self.assertEqual(self.client.get(reverse("calidad_banco")).status_code, 403)
        self.client.force_login(self.docente)
        self.assertEqual(self.client.get(reverse("calidad_banco")).status_code, 200)
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(reverse("calidad_banco")).status_code, 403)

    def test_intervencion_asignacion_aislamiento_y_seguimiento_pre_post(self):
        estudiante = self.estudiantes[0]
        self.agregar_respuestas(estudiante, [False, True])
        self.client.force_login(self.docente)
        url = reverse("intervenciones_docente")
        datos = {
            "matricula": self.matricula.pk,
            "materia": "Matemáticas", "competencia": "Sumas",
            "objetivo": "Consolidar la suma de enteros",
            "actividades": "Resolver cinco ejercicios graduados",
            "fecha_revision": (timezone.localdate() + timedelta(days=15)).isoformat(),
        }
        self.assertEqual(self.client.post(url, datos).status_code, 302)
        plan = IntervencionAcademica.objects.get()
        self.assertEqual(plan.porcentaje_inicial, 50.0)
        self.assertEqual(plan.docente, self.docente)
        self.agregar_respuestas(estudiante, [True, True])
        self.assertEqual(self.client.post(
            reverse("cerrar_intervencion_docente", args=[plan.pk]),
            {"observacion": "Se completaron los ejercicios previstos."},
        ).status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.estado, "CERRADA")
        self.assertEqual(plan.porcentaje_final, 100.0)
        self.assertEqual(plan.variacion_pp, 50.0)
        self.client.force_login(self.usuarios[0])
        self.assertContains(self.client.get(reverse("mis_intervenciones")), "Consolidar")
        self.client.force_login(self.usuarios[1])
        self.assertNotContains(self.client.get(reverse("mis_intervenciones")), "Consolidar")
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.post(url, datos).status_code, 200)
        self.assertEqual(IntervencionAcademica.objects.count(), 1)
        self.assertEqual(self.client.post(
            reverse("cerrar_intervencion_docente", args=[plan.pk]),
            {"observacion": "No autorizado, debe rechazarse"},
        ).status_code, 404)

    def test_intervencion_fecha_pasada_se_rechaza(self):
        self.client.force_login(self.docente)
        res = self.client.post(reverse("intervenciones_docente"), {
            "matricula": self.matricula.pk, "materia": "Matemáticas",
            "competencia": "Sumas", "objetivo": "Mejorar",
            "actividades": "Resolver ejercicios",
            "fecha_revision": (timezone.localdate() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(res.status_code, 200)
        self.assertFalse(IntervencionAcademica.objects.exists())
