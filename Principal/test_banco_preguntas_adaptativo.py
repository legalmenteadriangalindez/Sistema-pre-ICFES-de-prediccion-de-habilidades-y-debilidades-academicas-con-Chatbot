"""Pruebas de curaduría humana, seguridad y adaptación con datos sintéticos."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Principal.models import (
    AnioLectivo, AsignacionDocenteCurso, Curso, Estudiante, Grado,
    IntentoEvaluacion, Matricula, PerfilUsuario, Persona, PreguntaBanco,
    RespuestaEvaluacion, Rol, Sexo,
)
from Principal.services.banco_adaptativo import seleccionar_adaptativas
from Principal.services.seguimiento import resumen_estudiante


class BancoDocenteAdaptativoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            "admin_banco", "banco-admin@example.test", "Prueba!2026"
        )
        cls.docente = User.objects.create_user("doc_banco", password="Prueba!2026")
        cls.revisor = User.objects.create_user("doc_revisor", password="Prueba!2026")
        cls.sin_curso = User.objects.create_user("doc_sin_curso", password="Prueba!2026")
        cls.alumnos = [
            User.objects.create_user(f"alumno_banco_{i}", password="Prueba!2026")
            for i in range(2)
        ]
        rol_docente = Rol.objects.create(nombre="DOCENTE")
        rol_estudiante = Rol.objects.create(nombre="ESTUDIANTE")
        for usuario in (cls.docente, cls.revisor, cls.sin_curso):
            perfil = PerfilUsuario.objects.create(user=usuario)
            perfil.roles.add(rol_docente)
        sexo = Sexo.objects.create(descripcion="Prueba banco")
        cls.estudiantes = []
        for i, usuario in enumerate(cls.alumnos):
            perfil = PerfilUsuario.objects.create(user=usuario)
            perfil.roles.add(rol_estudiante)
            persona = Persona.objects.create(
                perfil_user=perfil, nombre=f"Alumno{i}", apellido="Banco",
                documento=f"BANCO-{i}", fecha_nacimiento=date(2009, 1, 1),
                direccion="Prueba", telefono="00000000", sexo=sexo,
            )
            cls.estudiantes.append(Estudiante.objects.create(persona=persona))
        grado = Grado.objects.create(nombre="Once")
        curso = Curso.objects.create(nombre="A", grado=grado)
        anio = AnioLectivo.objects.create(
            anio=2026, fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31), activo=True,
        )
        for alumno in cls.estudiantes:
            Matricula.objects.create(estudiante=alumno, curso=curso, anio_lectivo=anio)
        for usuario in (cls.docente, cls.revisor):
            AsignacionDocenteCurso.objects.create(
                docente=usuario.perfilusuario, curso=curso, anio_lectivo=anio,
            )

    @staticmethod
    def formulario(enunciado="¿Cuál es el resultado de 2 + 2?", competencia="Aritmética"):
        return {
            "accion": "crear",
            "materia": "Matemáticas",
            "competencia": competencia,
            "evidencia": "Resuelve operaciones con números enteros.",
            "dificultad": "BASICA",
            "contexto": "Suma de números enteros.",
            "enunciado": enunciado,
            "opcion_a": "Uno",
            "opcion_b": "Cuatro",
            "opcion_c": "Cinco",
            "opcion_d": "Seis",
            "respuesta_correcta": "B",
            "explicacion": "Dos más dos es igual a cuatro.",
        }

    def nueva_pregunta(self, enunciado="¿Cuánto es 2 + 2?", estado="BORRADOR",
                       creador=None, competencia="Aritmética", materia="Matemáticas"):
        pregunta = PreguntaBanco(
            materia=materia, competencia=competencia, dificultad="BASICA",
            contexto="", enunciado=enunciado,
            opciones={"A": "1", "B": "4", "C": "5", "D": "6"},
            respuesta_correcta="B", explicacion="Dos más dos da cuatro.",
            creado_por=creador or self.docente, estado=estado,
        )
        pregunta.save()
        return pregunta

    def test_borrador_manual_aprobacion_por_otro_docente_y_rechazo_autorrevision(self):
        self.client.force_login(self.docente)
        response = self.client.post(reverse("banco_preguntas"), self.formulario())
        self.assertRedirects(response, reverse("banco_preguntas"))
        pregunta = PreguntaBanco.objects.get()
        self.assertEqual(pregunta.estado, "BORRADOR")
        self.assertEqual(pregunta.creado_por, self.docente)
        self.assertEqual(pregunta.opciones["B"], "Cuatro")
        self.assertEqual(self.client.post(
            reverse("enviar_pregunta_revision", args=[pregunta.pk])
        ).status_code, 302)
        self.assertEqual(self.client.get(
            reverse("revisar_pregunta_banco", args=[pregunta.pk])
        ).status_code, 403)
        self.assertEqual(self.client.get(
            reverse("practica_adaptativa")
        ).status_code, 403)  # docente sin perfil de estudiante
        self.client.force_login(self.revisor)
        revision = self.client.get(reverse("revisar_pregunta_banco", args=[pregunta.pk]))
        self.assertContains(revision, "Dos más dos es igual")
        self.assertEqual(self.client.post(
            reverse("revisar_pregunta_banco", args=[pregunta.pk]),
            {"accion": "aprobar", "observacion": "Clave revisada"},
        ).status_code, 302)
        pregunta.refresh_from_db()
        self.assertEqual(pregunta.estado, "APROBADA")
        self.assertEqual(pregunta.revisado_por, self.revisor)
        self.assertEqual(self.client.post(
            reverse("revisar_pregunta_banco", args=[pregunta.pk]), {"accion": "aprobar"}
        ).status_code, 403)
        self.assertEqual(self.client.get(
            reverse("editar_pregunta_banco", args=[pregunta.pk])
        ).status_code, 403)

    def test_duplicados_y_opciones_repetidas_se_rechazan(self):
        self.client.force_login(self.docente)
        self.assertEqual(self.client.post(
            reverse("banco_preguntas"), self.formulario()
        ).status_code, 302)
        duplicada = self.formulario("  ¿CUÁL  es el resultado de 2 + 2? ")
        respuesta = self.client.post(reverse("banco_preguntas"), duplicada)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(PreguntaBanco.objects.count(), 1)
        mala = self.formulario("¿Cuál es el resultado de 3 + 3?")
        mala["opcion_d"] = mala["opcion_c"]
        self.assertEqual(self.client.post(reverse("banco_preguntas"), mala).status_code, 200)
        self.assertEqual(PreguntaBanco.objects.count(), 1)

    def test_rechazo_exige_motivo_y_permite_reenvio_corregido(self):
        pregunta = self.nueva_pregunta(estado="EN_REVISION")
        self.client.force_login(self.revisor)
        url = reverse("revisar_pregunta_banco", args=[pregunta.pk])
        self.assertEqual(self.client.post(url, {
            "accion": "rechazar", "observacion": "corto",
        }).status_code, 400)
        self.assertEqual(self.client.post(url, {
            "accion": "rechazar", "observacion": "Corregir el distractor y el enunciado.",
        }).status_code, 302)
        pregunta.refresh_from_db()
        self.assertEqual(pregunta.estado, "RECHAZADA")
        self.client.force_login(self.docente)
        datos = self.formulario("¿Cuál es el resultado de 2 + 3?")
        datos.pop("accion")
        self.assertEqual(self.client.post(
            reverse("editar_pregunta_banco", args=[pregunta.pk]), datos,
        ).status_code, 302)
        self.assertEqual(self.client.post(
            reverse("enviar_pregunta_revision", args=[pregunta.pk]),
        ).status_code, 302)
        pregunta.refresh_from_db()
        self.assertEqual(pregunta.estado, "EN_REVISION")
        self.assertEqual(pregunta.observaciones_revision, "")

    def test_docente_sin_curso_y_estudiante_no_pueden_curar(self):
        for usuario in (self.sin_curso, self.alumnos[0]):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(reverse("banco_preguntas")).status_code, 403)
                self.assertEqual(self.client.post(
                    reverse("banco_preguntas"), self.formulario(),
                ).status_code, 403)
        self.assertFalse(PreguntaBanco.objects.exists())

    def test_generacion_con_ia_guarda_solo_borrador_no_aprobado(self):
        from Principal.view_modules.banco_preguntas import generar_borrador_ia

        self.client.force_login(self.docente)
        simulada = [{
            "pregunta": "¿Qué número es par?", "contexto": "",
            "competencia": "Números enteros",
            "opciones": {"A": "3", "B": "4", "C": "5", "D": "7"},
            "respuesta_correcta": "B",
            "explicacion": "Cuatro es un número par.",
        }]
        with patch(
            "Principal.services.gestion_view_test.generar_quizes", return_value=simulada
        ):
            objeto = generar_borrador_ia("Matemáticas", self.docente)
        self.assertEqual(objeto.origen, "IA")
        self.assertEqual(objeto.estado, "BORRADOR")
        self.assertEqual(PreguntaBanco.objects.filter(estado="APROBADA").count(), 0)

    def test_practica_usa_solo_aprobadas_no_revela_claves_y_califica_una_vez(self):
        self.nueva_pregunta(enunciado="Pregunta sin aprobación")
        aprobada = self.nueva_pregunta(
            enunciado="¿Cuánto es dos más dos?", estado="APROBADA",
        )
        self.client.force_login(self.alumnos[0])
        url = reverse("practica_adaptativa")
        inicio = self.client.post(url, {"accion": "iniciar"})
        self.assertContains(inicio, aprobada.enunciado)
        self.assertNotContains(inicio, "Pregunta sin aprobación")
        self.assertNotContains(inicio, "Dos más dos da cuatro.")
        self.assertNotContains(inicio, "Clave: B")
        self.assertNotContains(inicio, "respuesta_correcta")
        self.assertNotContains(inicio, 'value="4"')
        sesion = self.client.session["practica_adaptativa_activa"]
        self.assertEqual(len(sesion["preguntas"]), 1)
        self.assertEqual(sesion["preguntas"][0]["id_banco"], aprobada.pk)
        resultado = self.client.post(url, {
            "accion": "calificar", "respuesta_0": "B",
            "id_banco": "99999", "respuesta_correcta": "A",
        })
        self.assertEqual(resultado.context["resultado"]["porcentaje"], 100)
        self.assertContains(resultado, "1 de 1")
        intento = IntentoEvaluacion.objects.get(estudiante=self.estudiantes[0])
        self.assertEqual(intento.materia, "Práctica adaptativa")
        respuesta = RespuestaEvaluacion.objects.get(intento=intento)
        self.assertTrue(respuesta.es_correcta)
        self.assertEqual(respuesta.pregunta_banco_id, aprobada.pk)
        repetido = self.client.post(url, {"accion": "calificar", "respuesta_0": "B"})
        self.assertContains(repetido, "ya se calificó")
        self.assertEqual(IntentoEvaluacion.objects.count(), 1)
        self.assertEqual(resumen_estudiante(self.estudiantes[0])["areas"][0]["total"], 1)
        self.client.force_login(self.alumnos[1])
        self.assertNotIn("resultado", self.client.get(url).context)
        self.assertEqual(IntentoEvaluacion.objects.filter(
            estudiante=self.estudiantes[1]
        ).count(), 0)

    def test_seleccion_prioriza_competencia_debil_y_evade_repeticiones(self):
        aritmetica = self.nueva_pregunta(
            enunciado="Aritmética de refuerzo", estado="APROBADA",
            competencia="Aritmética",
        )
        self.nueva_pregunta(
            enunciado="Competencia secundaria", estado="APROBADA",
            competencia="Geometría",
        )
        alumno = self.estudiantes[0]
        intento = IntentoEvaluacion.objects.create(
            estudiante=alumno, materia="Matemáticas", total_preguntas=2, aciertos=0,
        )
        for n in (1, 2):
            RespuestaEvaluacion.objects.create(
                intento=intento, numero=n, competencia="Aritmética",
                enunciado="", pregunta="Ejercicio fallado",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
                respuesta_estudiante="A", respuesta_correcta="B",
                explicacion="Revisar", es_correcta=False,
            )
        preguntas, focos = seleccionar_adaptativas(alumno, cantidad=1)
        self.assertEqual(preguntas[0].pk, aritmetica.pk)
        self.assertEqual(focos[0]["competencia"], "aritmética")
        RespuestaEvaluacion.objects.create(
            intento=intento, numero=3, competencia="Aritmética",
            enunciado="", pregunta="Ejercicio usado",
            opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            respuesta_estudiante="A", respuesta_correcta="B",
            explicacion="Revisar", es_correcta=False, pregunta_banco=aritmetica,
        )
        preguntas, _ = seleccionar_adaptativas(alumno, cantidad=1)
        self.assertNotEqual(preguntas[0].pk, aritmetica.pk)

    def test_busqueda_filtra_por_materia_dificultad_y_evidencia(self):
        propia = self.nueva_pregunta(
            enunciado="¿Qué operación permite encontrar el total?",
            estado="APROBADA", materia="Matemáticas",
        )
        propia.evidencia = "Interpreta relaciones aritméticas"
        propia.save(update_fields=["evidencia"])
        otra = self.nueva_pregunta(
            enunciado="¿Cuál es la idea principal del texto?",
            estado="APROBADA", materia="Lectura Crítica",
        )
        self.client.force_login(self.docente)
        vista = self.client.get(reverse("banco_preguntas"), {
            "materia": "Matemáticas", "dificultad": "BASICA",
            "q": "relaciones aritméticas",
        })
        self.assertContains(vista, propia.enunciado)
        self.assertNotContains(vista, otra.enunciado)
        self.assertEqual(len(vista.context["publicadas"]), 1)

    def test_no_hay_banco_aprobado_muestra_alternativa(self):
        self.nueva_pregunta(estado="EN_REVISION")
        self.client.force_login(self.alumnos[0])
        vista = self.client.post(reverse("practica_adaptativa"), {"accion": "iniciar"})
        self.assertContains(vista, "no hay preguntas revisadas")
        self.assertFalse(IntentoEvaluacion.objects.exists())
