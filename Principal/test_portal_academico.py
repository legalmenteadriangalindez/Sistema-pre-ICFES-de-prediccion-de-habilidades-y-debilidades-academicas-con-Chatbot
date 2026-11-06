"""Cobertura del portal académico sin invocar Ollama ni redes externas."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Actividad, ActividadAsignada, Acudiente, AnioLectivo, AsignacionDocenteCurso, Carrera, Curso,
    Estudiante, EstudianteAcudiente, Grado, IntentoEvaluacion, Matricula,
    Materia, NivelAprendizaje, PerfilUsuario, Persona, RelacionAcudiente,
    RespuestaEvaluacion, RecomendacionVocacional, Rol, Sexo, Tema,
)
from .services.orientacion import PREGUNTAS, calcular_perfil
from .services.seguimiento import resumen_estudiante, plan_semanal


class PortalAcademicoTests(TestCase):
    def setUp(self):
        sexo = Sexo.objects.create(descripcion="Prueba portal")
        self.sexo = sexo
        self.estudiante, self.usuario = self._crear_estudiante("alumno_portal", "DOC-PORTAL-01")
        grado = Grado.objects.create(nombre="Undécimo")
        curso = Curso.objects.create(grado=grado, nombre="11A")
        anio = AnioLectivo.objects.create(anio=2026, fecha_inicio=date(2026, 1, 12), fecha_fin=date(2026, 11, 30), activo=True)
        self.matricula = Matricula.objects.create(estudiante=self.estudiante, curso=curso, anio_lectivo=anio)
        self.docente = User.objects.create_user("docente_portal", password="ClaveSegura!2026")
        perfil = PerfilUsuario.objects.create(user=self.docente)
        perfil.roles.add(Rol.objects.get_or_create(nombre="DOCENTE")[0])
        AsignacionDocenteCurso.objects.create(docente=perfil, curso=curso, anio_lectivo=anio)
        self.acudiente_usuario = User.objects.create_user("acudiente_portal", password="ClaveSegura!2026")
        perfil_acudiente = PerfilUsuario.objects.create(user=self.acudiente_usuario)
        perfil_acudiente.roles.add(Rol.objects.get_or_create(nombre="ACUDIENTE")[0])
        persona_acudiente = Persona.objects.create(perfil_user=perfil_acudiente, nombre="Familiar", apellido="Prueba", documento="DOC-PORTAL-02", fecha_nacimiento=date(1980, 1, 1), direccion="Dirección de prueba", telefono="3000000000", sexo=self.sexo)
        acudiente = Acudiente.objects.create(persona=persona_acudiente)
        relacion = RelacionAcudiente.objects.create(descripcion="Acudiente prueba")
        EstudianteAcudiente.objects.create(estudiante=self.estudiante, acudiente=acudiente, relacion=relacion)
        materia = Materia.objects.create(nombre="Matemáticas")
        tema = Tema.objects.create(materia=materia, nombre="Álgebra")
        nivel = NivelAprendizaje.objects.create(nombre="Básico")
        self.actividad = Actividad.objects.create(tema=tema, nivel=nivel, titulo="Practicar álgebra", descripcion="Resolver ecuaciones de prueba")

    def _crear_estudiante(self, username, documento):
        user = User.objects.create_user(username, password="ClaveSegura!2026")
        perfil = PerfilUsuario.objects.create(user=user)
        perfil.roles.add(Rol.objects.get_or_create(nombre="ESTUDIANTE")[0])
        persona = Persona.objects.create(perfil_user=perfil, nombre="Ana", apellido="Prueba", documento=documento, fecha_nacimiento=date(2008, 1, 1), direccion="Dirección de prueba", telefono="3000000001", sexo=self.sexo)
        return Estudiante.objects.create(persona=persona), user

    def test_orientacion_valida_y_guarda_recomendaciones_repetibles(self):
        self.client.force_login(self.usuario)
        respuestas = {codigo: "5" if area == "tecnologia" else "2" for codigo, area, _ in PREGUNTAS}
        response = self.client.post(reverse("orientacion_vocacional"), respuestas)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["resultado"]["carreras"]), 5)
        self.assertEqual(RecomendacionVocacional.objects.filter(matricula=self.matricula).count(), 5)
        self.assertIn("Ingeniería", response.context["resultado"]["carreras"][0]["nombre"])
        self.client.post(reverse("orientacion_vocacional"), respuestas)
        self.assertEqual(RecomendacionVocacional.objects.filter(matricula=self.matricula).count(), 5)

    def test_orientacion_no_acepta_respuestas_incompletas(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse("orientacion_vocacional"), {"t1": "4"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["error"])
        self.assertFalse(RecomendacionVocacional.objects.exists())

    def test_comparador_limita_la_seleccion_a_tres(self):
        carreras = [Carrera.objects.create(nombre=f"Carrera {i}") for i in range(4)]
        self.client.force_login(self.usuario)
        consulta = "&".join("carrera=%s" % c.pk for c in carreras)
        response = self.client.get(reverse("comparadorDeCarreras") + "?" + consulta)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["seleccionadas"]), 3)

    def test_docente_puede_asignar_pero_estudiante_no(self):
        ruta = reverse("panel_docente")
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.post(ruta, {"matricula": self.matricula.pk, "actividad": self.actividad.pk}).status_code, 403)
        self.assertFalse(ActividadAsignada.objects.exists())
        self.client.force_login(self.docente)
        for _ in range(2):
            response = self.client.post(ruta, {"matricula": self.matricula.pk, "actividad": self.actividad.pk})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(ActividadAsignada.objects.count(), 1)

    def test_acudiente_solo_ve_estudiantes_vinculados(self):
        otro, _ = self._crear_estudiante("otro_alumno", "DOC-PORTAL-03")
        self.client.force_login(self.acudiente_usuario)
        r = self.client.get(reverse("acudiente"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["hijos"]), 1)
        self.assertEqual(r.context["hijos"][0]["estudiante"].pk, self.estudiante.pk)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("acudiente")).status_code, 403)

    def test_diagnostico_y_plan_derivados_de_resultados_reales(self):
        intento = IntentoEvaluacion.objects.create(estudiante=self.estudiante, materia="Matemáticas", total_preguntas=4, aciertos=1)
        for i in range(4):
            RespuestaEvaluacion.objects.create(intento=intento, numero=i, competencia="Álgebra", enunciado="", pregunta=f"Pregunta {i}", opciones={"A": "uno", "B": "dos"}, respuesta_estudiante="A", respuesta_correcta="B" if i else "A", explicacion="", es_correcta=i == 0)
        resumen = resumen_estudiante(self.estudiante)
        self.assertEqual(resumen["areas"][0]["porcentaje"], 25.0)
        self.assertEqual(resumen["areas"][0]["prioridad"], "Practicar")
        self.assertEqual(len(plan_semanal(resumen)), 7)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("diagnostico_academico")).status_code, 200)
        self.assertEqual(self.client.get(reverse("plan_semanal")).status_code, 200)

    def test_acceso_por_rol_desde_inicio(self):
        self.client.force_login(self.docente)
        self.assertRedirects(self.client.get(reverse("home")), reverse("panel_docente"), fetch_redirect_response=False)
        self.client.force_login(self.acudiente_usuario)
        self.assertRedirects(self.client.get(reverse("home")), reverse("acudiente"), fetch_redirect_response=False)

    def test_integral_ampliado_contiene_cincuenta_preguntas_sin_claves(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Integral ampliado"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["preguntas"]), 50)
        self.assertEqual(len({p["materia"] for p in response.context["preguntas"]}), 5)
        self.assertTrue(all("correcta" not in p for p in response.context["preguntas"]))

    def test_algoritmo_no_afirma_probabilidades_de_exito(self):
        respuestas = {codigo: "3" for codigo, _, _ in PREGUNTAS}
        areas, carreras = calcular_perfil(respuestas)
        self.assertEqual(set(areas), {"tecnologia", "salud", "social", "creatividad"})
        self.assertTrue(all(0 <= r["afinidad"] <= 100 for r in carreras))
