"""Pruebas sintéticas: repaso, consentimiento, progreso y datos administrativos."""
from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from Principal.models import (
    Acudiente, AnioLectivo, AsignacionDocenteCurso, ConsentimientoTutorIA,
    Curso, Estudiante, EstudianteAcudiente, Grado, IntentoEvaluacion, Matricula,
    NotificacionAcademica, PerfilUsuario, Persona, PreguntaBanco,
    RegistroAuditoria, RelacionAcudiente, RepasoEspaciado,
    RespuestaEvaluacion, Rol, Sexo,
)
from Principal.services.analisis_progreso import comparar_progreso
from Principal.services.evaluaciones import calificar_y_guardar_evaluacion
from Principal.services.fuentes_validadas import contexto_con_fuentes
from Principal.services.privacidad_educativa import tutor_autorizado
from Principal.services.repasos_espaciados import repasos_pendientes


class MejorasPrioritariasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin_nuevo", "admin@example.test", "Clave!2026")
        cls.docente = User.objects.create_user("doc_nuevo", password="Clave!2026")
        cls.ajeno = User.objects.create_user("doc_ajeno_nuevo", password="Clave!2026")
        cls.padre = User.objects.create_user("acudiente_nuevo", password="Clave!2026")
        cls.alumnos = [
            User.objects.create_user(f"alumno_nuevo_{i}", password="Clave!2026")
            for i in range(3)
        ]
        roles = {nombre: Rol.objects.create(nombre=nombre) for nombre in ("DOCENTE", "ESTUDIANTE", "ACUDIENTE")}
        for usuario, rol in [
            (cls.docente, "DOCENTE"), (cls.ajeno, "DOCENTE"), (cls.padre, "ACUDIENTE"),
            *[(alumno, "ESTUDIANTE") for alumno in cls.alumnos],
        ]:
            perfil = PerfilUsuario.objects.create(user=usuario)
            perfil.roles.add(roles[rol])
        sexo = Sexo.objects.create(descripcion="Prueba privada")
        cls.estudiantes = []
        for i, alumno in enumerate(cls.alumnos):
            persona = Persona.objects.create(
                perfil_user=alumno.perfilusuario, nombre=f"Alumno{i}",
                apellido="Cierre", documento=f"REP-TEST-{i}",
                fecha_nacimiento=date(2009, 1, 1),
                direccion="Prueba", telefono="000000", sexo=sexo,
            )
            cls.estudiantes.append(Estudiante.objects.create(persona=persona))
        persona = Persona.objects.create(
            perfil_user=cls.padre.perfilusuario,
            nombre="Acudiente", apellido="Prueba", documento="ACU-TEST-2026",
            fecha_nacimiento=date(1979, 1, 1), direccion="Prueba",
            telefono="000000", sexo=sexo,
        )
        acudiente = Acudiente.objects.create(persona=persona)
        relacion = RelacionAcudiente.objects.create(descripcion="Responsable")
        EstudianteAcudiente.objects.create(
            estudiante=cls.estudiantes[0], acudiente=acudiente, relacion=relacion,
        )
        grado = Grado.objects.create(nombre="Once")
        cls.curso = Curso.objects.create(grado=grado, nombre="A", cupo_maximo=2)
        cls.otro_curso = Curso.objects.create(grado=grado, nombre="B", cupo_maximo=3)
        cls.anio = AnioLectivo.objects.create(
            anio=2026, fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31), activo=True,
        )
        cls.otro_anio = AnioLectivo.objects.create(
            anio=2027, fecha_inicio=date(2027, 1, 1),
            fecha_fin=date(2027, 12, 31), activo=False,
        )
        cls.matricula = Matricula.objects.create(
            estudiante=cls.estudiantes[0], curso=cls.curso, anio_lectivo=cls.anio,
        )
        Matricula.objects.create(
            estudiante=cls.estudiantes[1], curso=cls.otro_curso, anio_lectivo=cls.anio,
        )
        AsignacionDocenteCurso.objects.create(
            docente=cls.docente.perfilusuario, curso=cls.curso,
            anio_lectivo=cls.anio,
        )
        cls.pregunta = PreguntaBanco.objects.create(
            materia="Matemáticas", competencia="Fracciones",
            enunciado="¿Cuál es una fracción equivalente?",
            opciones={"A": "1/3", "B": "2/4", "C": "1/5", "D": "3/5"},
            respuesta_correcta="B", explicacion="Dos cuartos equivalen a un medio.",
            estado="APROBADA", activo=True, creado_por=cls.docente,
        )

    def contestar(self, correcta):
        pregunta = self.pregunta
        return calificar_y_guardar_evaluacion(
            estudiante=self.estudiantes[0], materia="Práctica adaptativa",
            preguntas=[{
                "id": 0, "id_banco": pregunta.pk,
                "competencia": "Matemáticas · Fracciones",
                "contexto": "", "pregunta": pregunta.enunciado,
                "opciones": pregunta.opciones,
                "respuesta_correcta": pregunta.respuesta_correcta,
                "explicacion": pregunta.explicacion,
            }],
            datos_respuesta={"respuesta_0": "B" if correcta else "A"},
        )

    def test_repaso_se_programa_solo_para_pregunta_aprobada(self):
        self.contestar(False)
        repaso = RepasoEspaciado.objects.get(estudiante=self.estudiantes[0])
        self.assertEqual(repaso.intervalo_dias, 1)
        self.contestar(True)
        repaso.refresh_from_db()
        self.assertEqual(repaso.intervalo_dias, 1)
        self.contestar(True)
        repaso.refresh_from_db()
        self.assertEqual(repaso.intervalo_dias, 3)
        self.assertEqual(RepasoEspaciado.objects.count(), 1)
        self.assertFalse(repasos_pendientes(self.estudiantes[0]).exists())
        self.client.force_login(self.alumnos[0])
        self.assertContains(self.client.get(reverse("agenda_repasos")), "Fracciones")
        self.client.force_login(self.alumnos[1])
        self.assertNotContains(self.client.get(reverse("agenda_repasos")), "Fracciones")

    def test_progreso_muestra_insuficiencia_y_no_ve_alumno_ajeno(self):
        alumno = self.estudiantes[0]
        self.assertEqual(comparar_progreso(alumno), [])
        for i in range(6):
            self.contestar(i >= 3)
        resultados = comparar_progreso(alumno)
        self.assertEqual(resultados[0]["antes"], 0)
        self.assertEqual(resultados[0]["despues"], 100)
        self.client.force_login(self.docente)
        self.assertContains(self.client.get(
            reverse("progreso_competencias") + f"?matricula={self.matricula.pk}",
        ), "Fracciones")
        otra_matricula = Matricula.objects.get(estudiante=self.estudiantes[1])
        self.assertEqual(self.client.get(
            reverse("progreso_competencias") + f"?matricula={otra_matricula.pk}",
        ).status_code, 404)
        self.client.force_login(self.alumnos[1])
        self.assertNotContains(self.client.get(reverse("progreso_competencias")), "Fracciones")

    def test_tutor_usa_solo_fuentes_aprobadas_y_bloquea_menores_sin_permiso(self):
        self.assertFalse(tutor_autorizado(self.estudiantes[0]))
        texto, fuentes = contexto_con_fuentes(
            self.estudiantes[0], "Explícame fracciones con ejercicios"
        )
        self.assertIn(f"[B-{self.pregunta.pk}]", texto)
        self.assertEqual(fuentes[0]["id"], self.pregunta.pk)
        self.client.force_login(self.alumnos[0])
        self.assertEqual(self.client.get(
            reverse("material_validado", args=[self.pregunta.pk]),
        ).status_code, 200)
        self.client.force_login(self.padre)
        self.assertEqual(self.client.post(reverse("consentimiento_tutor"), {
            "estudiante": self.estudiantes[1].pk, "decision": "autorizar",
        }).status_code, 404)
        self.assertEqual(self.client.post(reverse("consentimiento_tutor"), {
            "estudiante": self.estudiantes[0].pk, "decision": "autorizar",
        }).status_code, 302)
        self.assertTrue(tutor_autorizado(self.estudiantes[0]))
        self.assertTrue(ConsentimientoTutorIA.objects.get(
            estudiante=self.estudiantes[0]
        ).autorizado)
        self.assertEqual(self.client.post(reverse("consentimiento_tutor"), {
            "estudiante": self.estudiantes[0].pk, "decision": "revocar",
        }).status_code, 302)
        self.assertFalse(tutor_autorizado(self.estudiantes[0]))
        self.assertEqual(RegistroAuditoria.objects.filter(
            accion__startswith="TUTOR_IA_",
        ).count(), 2)

    def test_no_se_exponen_borradores_ni_material_durante_simulacro(self):
        pregunta = PreguntaBanco.objects.create(
            materia="Matemáticas", competencia="Fracciones",
            enunciado="Borrador privado sobre fracciones",
            opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            respuesta_correcta="A", explicacion="No revisado",
            estado="BORRADOR",
        )
        texto, _ = contexto_con_fuentes(
            self.estudiantes[0], "Explícame fracciones"
        )
        self.assertNotIn(pregunta.enunciado, texto)
        self.client.force_login(self.alumnos[0])
        self.assertEqual(self.client.get(
            reverse("material_validado", args=[pregunta.pk]),
        ).status_code, 404)

    def test_importacion_csv_primero_valida_y_exportacion_docente_se_filtra(self):
        self.client.force_login(self.admin)
        url = reverse("cargar_matriculas")
        archivo = SimpleUploadedFile(
            "nuevas.csv",
            b"documento,curso_id,anio\nREP-TEST-2,9999,2027\n",
            content_type="text/csv",
        )
        self.assertEqual(self.client.post(url, {"archivo": archivo}).status_code, 200)
        self.assertEqual(Matricula.objects.count(), 2)
        contenido = f"documento,curso_id,anio\nREP-TEST-2,{self.curso.pk},2027\n".encode()
        archivo = SimpleUploadedFile("validas.csv", contenido, content_type="text/csv")
        self.assertEqual(self.client.post(url, {"archivo": archivo}).status_code, 302)
        self.assertTrue(Matricula.objects.filter(
            estudiante=self.estudiantes[2], anio_lectivo=self.otro_anio,
        ).exists())
        self.client.force_login(self.docente)
        reporte = self.client.get(reverse("exportar_reporte_matriculas"))
        self.assertEqual(reporte.status_code, 200)
        texto = reporte.content.decode("utf-8-sig")
        self.assertIn("REP-TEST-0", texto)
        self.assertNotIn("REP-TEST-1", texto)
        self.assertTrue(RegistroAuditoria.objects.filter(
            actor=self.docente, accion="EXPORTACION_ACADEMICA",
        ).exists())
        self.client.force_login(self.alumnos[0])
        self.assertEqual(self.client.get(reverse("exportar_reporte_matriculas")).status_code, 403)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_notificaciones_privadas_y_preferencias(self):
        from Principal.services.avisos_academicos import emitir_aviso

        usuario = self.alumnos[0]
        aviso = emitir_aviso(
            usuario, "ACTIVIDAD", "Práctica pendiente", "Revisa tu actividad.",
            "actividad-prueba",
        )
        emitir_aviso(
            usuario, "ACTIVIDAD", "Práctica pendiente", "Revisa tu actividad.",
            "actividad-prueba",
        )
        self.assertEqual(NotificacionAcademica.objects.count(), 1)
        self.client.force_login(self.alumnos[1])
        self.assertEqual(self.client.post(
            reverse("marcar_aviso_leido", args=[aviso.pk]),
        ).status_code, 404)
        self.assertNotContains(self.client.get(reverse("mis_avisos")), "Práctica pendiente")
        self.client.force_login(usuario)
        self.assertContains(self.client.get(reverse("mis_avisos")), "Práctica pendiente")
        self.assertEqual(self.client.post(
            reverse("marcar_aviso_leido", args=[aviso.pk]),
        ).status_code, 302)
        aviso.refresh_from_db()
        self.assertIsNotNone(aviso.leida_en)
        self.client.post(reverse("mis_avisos"), {"accion": "preferencias"})
        self.assertIsNone(emitir_aviso(
            usuario, "ACTIVIDAD", "Otro aviso", "No permitido",
            "actividad-nueva",
        ))
