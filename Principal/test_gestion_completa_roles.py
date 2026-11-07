"""Regresiones de las operaciones completas de docente y administrador.

Solo base de datos temporal de Django: no utiliza alumnos reales ni Ollama.
"""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Principal.models import (
    Actividad, ActividadAsignada, Acudiente, AnioLectivo, AsignacionDocenteCurso,
    Curso, Estudiante, EstudianteAcudiente, Grado, IntentoEvaluacion,
    Materia, Matricula, NivelAprendizaje, PerfilUsuario, Persona,
    RelacionAcudiente, RetroalimentacionDocente, Rol, Sexo, Tema,
)


class GestionEscolarIntegralTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            "admin_integral", "admin-integral@example.test", "Demo!Segura2026"
        )
        cls.docente = User.objects.create_user("doc_integral", password="Demo!Segura2026")
        cls.docente_ajeno = User.objects.create_user("doc_otro", password="Demo!Segura2026")
        cls.guardián = User.objects.create_user("acudiente_integral", password="Demo!Segura2026")
        cls.alumnos = [
            User.objects.create_user(f"alumno_integral_{i}", password="Demo!Segura2026")
            for i in range(2)
        ]
        for usuario, rol in [
            (cls.docente, "DOCENTE"), (cls.docente_ajeno, "DOCENTE"),
            (cls.guardián, "ACUDIENTE"),
            *[(a, "ESTUDIANTE") for a in cls.alumnos],
        ]:
            perfil = PerfilUsuario.objects.create(user=usuario)
            rol_obj, _ = Rol.objects.get_or_create(nombre=rol)
            perfil.roles.add(rol_obj)
        sexo = Sexo.objects.create(descripcion="Prueba de administración")
        cls.estudiantes = []
        for i, usuario in enumerate(cls.alumnos):
            persona = Persona.objects.create(
                perfil_user=usuario.perfilusuario, nombre=f"Alumno{i}",
                apellido="Prueba", documento=f"INT-CIERRE-{i}",
                fecha_nacimiento=date(2008, 1, 1),
                direccion="Test", telefono="0000000", sexo=sexo,
            )
            cls.estudiantes.append(Estudiante.objects.create(persona=persona))
        persona_acudiente = Persona.objects.create(
            perfil_user=cls.guardián.perfilusuario, nombre="Acudiente",
            apellido="Prueba", documento="INT-ACUDIENTE",
            fecha_nacimiento=date(1980, 1, 1), direccion="Test",
            telefono="0000000", sexo=sexo,
        )
        cls.acudiente = Acudiente.objects.create(persona=persona_acudiente)
        cls.relacion = RelacionAcudiente.objects.create(descripcion="Responsable")
        cls.grado = Grado.objects.create(nombre="Once")
        cls.curso = Curso.objects.create(grado=cls.grado, nombre="A", cupo_maximo=1)
        cls.curso_b = Curso.objects.create(grado=cls.grado, nombre="B", cupo_maximo=3)
        cls.anio = AnioLectivo.objects.create(
            anio=2026, fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31), activo=True,
        )
        cls.matricula = Matricula.objects.create(
            estudiante=cls.estudiantes[0], curso=cls.curso, anio_lectivo=cls.anio
        )
        AsignacionDocenteCurso.objects.create(
            docente=cls.docente.perfilusuario, curso=cls.curso, anio_lectivo=cls.anio,
        )
        materia = Materia.objects.create(nombre="Matemáticas")
        cls.tema = Tema.objects.create(materia=materia, nombre="Álgebra")
        cls.nivel = NivelAprendizaje.objects.create(nombre="Básico")
        cls.actividad_legacy = Actividad.objects.create(
            titulo="Legado", descripcion="Sin autor", tema=cls.tema, nivel=cls.nivel,
        )

    def test_docente_crea_con_autoria_y_edita_solo_lo_propio(self):
        self.client.force_login(self.docente)
        respuesta = self.client.post(reverse("panel_docente"), {
            "accion": "crear", "titulo": "Tarea propia",
            "descripcion": "Resolver una práctica de álgebra",
            "tema": self.tema.pk, "nivel": self.nivel.pk,
        })
        self.assertEqual(respuesta.status_code, 200)
        actividad = Actividad.objects.get(titulo="Tarea propia")
        self.assertEqual(actividad.creado_por, self.docente)
        url = reverse("editar_actividad_docente", args=[actividad.pk])
        self.assertEqual(self.client.post(url, {
            "titulo": "Tarea editada", "descripcion": "Nueva práctica",
            "tema": self.tema.pk, "nivel": self.nivel.pk, "activo": "on",
        }).status_code, 302)
        actividad.refresh_from_db()
        self.assertEqual(actividad.titulo, "Tarea editada")
        self.assertEqual(
            self.client.get(reverse("editar_actividad_docente", args=[self.actividad_legacy.pk])).status_code,
            403,
        )
        self.client.force_login(self.docente_ajeno)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_docente_retiro_pendiente_y_no_modifica_trabajo_completado(self):
        self.client.force_login(self.docente)
        url = reverse("panel_docente")
        self.assertEqual(self.client.post(url, {
            "matricula": self.matricula.pk, "actividad": self.actividad_legacy.pk,
        }).status_code, 200)
        asignada = ActividadAsignada.objects.get(matricula=self.matricula)
        self.assertEqual(asignada.asignada_por, self.docente)
        self.assertEqual(self.client.post(url, {
            "accion": "retirar", "asignacion_id": asignada.pk,
        }).status_code, 302)
        self.assertFalse(ActividadAsignada.objects.filter(pk=asignada.pk).exists())
        asignada = ActividadAsignada.objects.create(
            matricula=self.matricula, actividad=self.actividad_legacy,
            asignada_por=self.docente, completada=True,
        )
        self.assertEqual(self.client.post(url, {
            "accion": "retirar", "asignacion_id": asignada.pk,
        }).status_code, 200)
        self.assertTrue(ActividadAsignada.objects.filter(pk=asignada.pk).exists())

    def test_comentario_visible_solo_para_estudiante_autorizado(self):
        self.client.force_login(self.docente)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "accion": "retroalimentar", "matricula": self.matricula.pk,
            "texto": "Refuerza los ejercicios de proporcionalidad.",
        }).status_code, 200)
        self.assertEqual(RetroalimentacionDocente.objects.count(), 1)
        self.client.force_login(self.alumnos[0])
        propio = self.client.get(reverse("actividadesUsuario"))
        self.assertContains(propio, "proporcionalidad")
        self.client.force_login(self.alumnos[1])
        ajeno = self.client.get(reverse("actividadesUsuario"))
        self.assertNotContains(ajeno, "proporcionalidad")

    def test_docente_ajeno_no_puede_ver_reportes_ni_ficha(self):
        detalle = reverse("detalle_estudiante_docente", args=[self.matricula.pk])
        self.client.force_login(self.docente)
        self.assertEqual(self.client.get(detalle).status_code, 200)
        self.client.force_login(self.docente_ajeno)
        self.assertEqual(self.client.get(detalle).status_code, 404)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "accion": "retroalimentar", "matricula": self.matricula.pk,
            "texto": "No debe guardarse para un curso ajeno",
        }).status_code, 403)
        self.assertEqual(RetroalimentacionDocente.objects.count(), 0)

    def test_administrador_edita_usuario_y_persona(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(
            reverse("admin_editar_usuario", args=[self.alumnos[0].pk]),
            {"username": self.alumnos[0].username, "email": "nuevo@example.test",
             "first_name": "Nuevo", "last_name": "Nombre"},
        ).status_code, 302)
        self.alumnos[0].refresh_from_db()
        self.assertEqual(self.alumnos[0].email, "nuevo@example.test")
        persona = self.estudiantes[0].persona
        self.assertEqual(self.client.post(
            reverse("admin_editar_persona", args=[persona.pk]),
            {"nombre": "Renovado", "apellido": "Prueba", "documento": persona.documento,
             "fecha_nacimiento": "2008-01-01", "direccion": "Test", "telefono": "0000000",
             "sexo": persona.sexo_id},
        ).status_code, 302)
        persona.refresh_from_db()
        self.assertEqual(persona.nombre, "Renovado")

    def test_matricula_cupo_unicidad_edicion_y_reporte(self):
        self.client.force_login(self.admin)
        url = reverse("admin_matriculas_familias")
        bloqueada = self.client.post(url, {
            "tipo": "matricula", "estudiante": self.estudiantes[1].pk,
            "curso": self.curso.pk, "anio_lectivo": self.anio.pk, "activa": "on",
        })
        self.assertEqual(bloqueada.status_code, 200)
        self.assertEqual(Matricula.objects.count(), 1)
        creada = self.client.post(url, {
            "tipo": "matricula", "estudiante": self.estudiantes[1].pk,
            "curso": self.curso_b.pk, "anio_lectivo": self.anio.pk, "activa": "on",
        })
        self.assertEqual(creada.status_code, 302)
        otra = Matricula.objects.get(estudiante=self.estudiantes[1])
        self.assertEqual(self.client.post(
            reverse("admin_editar_matricula", args=[otra.pk]),
            {"estudiante": otra.estudiante_id, "curso": otra.curso_id,
             "anio_lectivo": otra.anio_lectivo_id},
        ).status_code, 302)
        otra.refresh_from_db()
        self.assertFalse(otra.activa)
        reporte = self.client.get(reverse("admin_reportes_academicos"))
        self.assertEqual(reporte.status_code, 200)
        self.assertEqual(reporte.context["total_matriculas_activas"], 1)

    def test_post_manipulado_no_reasigna_matricula_ni_historias(self):
        self.client.force_login(self.admin)
        original = self.matricula
        intento = IntentoEvaluacion.objects.create(
            estudiante=self.estudiantes[0], materia="Matemáticas",
            total_preguntas=10, aciertos=7,
        )
        asignada = ActividadAsignada.objects.create(
            matricula=original, actividad=self.actividad_legacy, completada=True,
        )
        # La petición intenta transferir identidad y curso al alumno ajeno.
        respuesta = self.client.post(reverse("admin_editar_matricula", args=[original.pk]), {
            "estudiante": self.estudiantes[1].pk,
            "curso": self.curso_b.pk,
            "anio_lectivo": self.anio.pk,
            "activa": "on",
        })
        self.assertEqual(respuesta.status_code, 200)
        original.refresh_from_db()
        self.assertEqual(original.estudiante_id, self.estudiantes[0].pk)
        self.assertEqual(original.curso_id, self.curso.pk)
        self.assertEqual(IntentoEvaluacion.objects.get(pk=intento.pk).estudiante_id, self.estudiantes[0].pk)
        self.assertTrue(ActividadAsignada.objects.filter(pk=asignada.pk).exists())

    def test_vinculos_familiares_crear_editar_y_revocar(self):
        self.client.force_login(self.admin)
        url = reverse("admin_matriculas_familias")
        self.assertEqual(self.client.post(url, {
            "tipo": "vinculo", "estudiante": self.estudiantes[0].pk,
            "acudiente": self.acudiente.pk, "relacion": self.relacion.pk,
        }).status_code, 302)
        vinculo = EstudianteAcudiente.objects.get()
        self.assertEqual(self.client.get(
            reverse("admin_editar_vinculo", args=[vinculo.pk])
        ).status_code, 200)
        self.assertEqual(self.client.post(
            reverse("admin_desvincular_familiar", args=[vinculo.pk])
        ).status_code, 302)
        self.assertFalse(EstudianteAcudiente.objects.exists())

    def test_eliminacion_curso_en_uso_no_borra_matriculas(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(
            reverse("eliminar_admin_gestion_academico", args=["cursos", self.curso.pk])
        ).status_code, 302)
        self.assertTrue(Curso.objects.filter(pk=self.curso.pk).exists())
        self.assertTrue(Matricula.objects.filter(pk=self.matricula.pk).exists())

    def test_estudiante_no_modifica_catalogos_ni_consulta_reportes(self):
        self.client.force_login(self.alumnos[0])
        self.assertNotEqual(self.client.get(reverse("admin_reportes_academicos")).status_code, 200)
        self.assertNotEqual(self.client.post(
            reverse("admin_editar_catalogo", args=["grados", self.grado.pk]),
            {"nombre": "Otro"},
        ).status_code, 200)
        self.grado.refresh_from_db()
        self.assertEqual(self.grado.nombre, "Once")
