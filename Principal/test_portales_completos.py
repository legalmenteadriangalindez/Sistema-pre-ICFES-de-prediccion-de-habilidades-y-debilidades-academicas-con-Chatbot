"""Pruebas de los flujos añadidos: cursos autorizados, familia, vocación y planes.
No hay llamadas a Ollama ni dependencia de servicios externos.
"""
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    Acudiente, Actividad, ActividadAsignada, AnioLectivo, Carrera, Curso,
    DocenteCurso, Estudiante, EstudianteAcudiente, Grado, IntentoEvaluacion,
    Matricula, NivelAprendizaje, PerfilUsuario, Persona, RecomendacionVocacional,
    RelacionAcudiente, Rol, Sexo, Tema, Materia,
)
from .services.seguimiento_academico import plan_semanal, resumen_de_intentos


class PortalesCompletosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sexo = Sexo.objects.create(descripcion='Prueba')
        cls.grado = Grado.objects.create(nombre='Décimo')
        cls.curso = Curso.objects.create(grado=cls.grado, nombre='10A')
        cls.otro_curso = Curso.objects.create(grado=cls.grado, nombre='10B')
        cls.anio = AnioLectivo.objects.create(anio=2026, fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 1), activo=True)
        cls.admin = cls.usuario('admin', 'ADMIN', superuser=True)
        cls.docente = cls.usuario('docente', 'DOCENTE')
        cls.estudiante = cls.usuario('est1', 'ESTUDIANTE', estudiante=True)
        cls.ajeno = cls.usuario('est2', 'ESTUDIANTE', estudiante=True)
        cls.acudiente = cls.usuario('acudiente', 'ACUDIENTE', familiar=True)
        cls.otro_acudiente = cls.usuario('otro_acudiente', 'ACUDIENTE', familiar=True)
        cls.matricula = Matricula.objects.create(estudiante=cls.estudiante.estudiante, curso=cls.curso, anio_lectivo=cls.anio)
        cls.matricula_ajena = Matricula.objects.create(estudiante=cls.ajeno.estudiante, curso=cls.otro_curso, anio_lectivo=cls.anio)
        cls.relacion = RelacionAcudiente.objects.create(descripcion='Madre')
        EstudianteAcudiente.objects.create(estudiante=cls.estudiante.estudiante, acudiente=cls.acudiente.acudiente, relacion=cls.relacion)
        EstudianteAcudiente.objects.create(estudiante=cls.ajeno.estudiante, acudiente=cls.otro_acudiente.acudiente, relacion=cls.relacion)
        cls.materia = Materia.objects.create(nombre='Matemáticas')
        cls.nivel = NivelAprendizaje.objects.create(nombre='Medio')
        cls.tema = Tema.objects.create(materia=cls.materia, nombre='Álgebra')
        cls.actividad = Actividad.objects.create(tema=cls.tema, nivel=cls.nivel, titulo='Repasar ecuaciones', descripcion='Resolver ejercicios de práctica.')

    @classmethod
    def usuario(cls, username, rol, superuser=False, estudiante=False, familiar=False):
        user = get_user_model().objects.create_user(username=username, password='ClavePrueba!2026', is_staff=superuser, is_superuser=superuser)
        perfil = PerfilUsuario.objects.create(user=user)
        perfil.roles.add(Rol.objects.get_or_create(nombre=rol)[0])
        persona = Persona.objects.create(perfil_user=perfil, nombre=username, apellido='Ejemplo', documento='DOC-'+username, fecha_nacimiento=date(2008,1,1), direccion='Prueba', telefono='3000000000', sexo=cls.sexo)
        user.persona_demo = persona
        if estudiante:
            user.estudiante = Estudiante.objects.create(persona=persona)
        if familiar:
            user.acudiente = Acudiente.objects.create(persona=persona)
        return user

    def test_docente_ve_solo_sus_estudiantes(self):
        DocenteCurso.objects.create(docente=self.docente, curso=self.curso)
        self.client.force_login(self.docente)
        response = self.client.get(reverse('panel_docente'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'est1 Ejemplo')
        self.assertNotContains(response, 'est2 Ejemplo')

    def test_docente_no_asigna_actividad_a_estudiante_ajeno(self):
        DocenteCurso.objects.create(docente=self.docente, curso=self.curso)
        self.client.force_login(self.docente)
        response = self.client.post(reverse('panel_docente'), {'accion': 'asignar_actividad', 'matricula_id': str(self.matricula_ajena.pk), 'actividad_id': str(self.actividad.pk)})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ActividadAsignada.objects.filter(matricula=self.matricula_ajena).exists())
        self.client.post(reverse('panel_docente'), {'accion': 'asignar_actividad', 'matricula_id': str(self.matricula.pk), 'actividad_id': str(self.actividad.pk)})
        self.assertTrue(ActividadAsignada.objects.filter(matricula=self.matricula).exists())

    def test_acudiente_solo_ve_sus_hijos(self):
        self.client.force_login(self.acudiente)
        response = self.client.get(reverse('panel_acudiente'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'est1 Ejemplo')
        self.assertNotContains(response, 'est2 Ejemplo')

    def test_estudiante_no_ve_paneles_de_docentes(self):
        self.client.force_login(self.estudiante)
        self.assertNotEqual(self.client.get(reverse('panel_docente')).status_code, 200)
        self.assertNotEqual(self.client.get(reverse('gestion_docentes')).status_code, 200)
        self.assertNotEqual(self.client.get(reverse('panel_acudiente')).status_code, 200)

    def test_admin_asigna_curso_que_habilita_panel_docente(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('gestion_docentes'), {'accion': 'asignar', 'docente_id': str(self.docente.pk), 'curso_id': str(self.curso.pk)})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DocenteCurso.objects.filter(docente=self.docente, curso=self.curso).exists())

    def test_cuestionario_vocacional_rechaza_respuestas_incompletas(self):
        self.client.force_login(self.estudiante)
        response = self.client.post(reverse('orientacion_vocacional'), {'t1': '5'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RecomendacionVocacional.objects.count(), 0)

    def test_cuestionario_vocacional_guarda_afinidad_sin_duplicados(self):
        from .orientacion_views import PREGUNTAS_VOCACIONALES
        self.client.force_login(self.estudiante)
        respuestas = {clave: '5' if categoria == 'tecnologia' else '2' for clave, _, categoria in PREGUNTAS_VOCACIONALES}
        for _ in range(2):
            respuesta = self.client.post(reverse('orientacion_vocacional'), respuestas)
            self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(RecomendacionVocacional.objects.filter(matricula=self.matricula).count(), 4)
        sistemas = RecomendacionVocacional.objects.get(matricula=self.matricula, carrera__nombre='Ingeniería de Sistemas')
        self.assertEqual(int(sistemas.compatibilidad), 100)
        self.assertFalse(RecomendacionVocacional.objects.filter(matricula=self.matricula_ajena).exists())

    def test_comparador_limita_a_tres_carreras(self):
        self.client.force_login(self.estudiante)
        response = self.client.get(reverse('comparadorDeCarreras') + '?carrera=1&carrera=2&carrera=3&carrera=4')
        self.assertEqual(response.status_code, 400)

    def test_plan_semanal_refleja_resultados_sin_pretender_ia(self):
        IntentoEvaluacion.objects.create(estudiante=self.estudiante.estudiante, materia='Matemáticas', total_preguntas=20, aciertos=8)
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('plan_estudio'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Matemáticas')
        resumen = resumen_de_intentos(IntentoEvaluacion.objects.filter(estudiante=self.estudiante.estudiante))
        item = next(x for x in resumen if x['area']=='Matemáticas')
        self.assertEqual(item['porcentaje'], 40.0)
        self.assertEqual(len(plan_semanal(resumen)), 6)

    def test_admin_puede_editar_curso_sin_borrar_matriculas(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('editar_catalogo', args=['cursos', self.curso.pk]), {
            'grado': self.grado.pk, 'nombre': '10C', 'cupo_maximo': 25, 'activo': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.nombre, '10C')
        self.assertTrue(Matricula.objects.filter(pk=self.matricula.pk).exists())
