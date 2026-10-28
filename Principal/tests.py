"""Pruebas de regresión de registro, permisos, CRUD y cuestionarios.

Los servicios de IA se sustituyen con mocks: estas pruebas no requieren Ollama.
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Estudiante, Grado, PerfilUsuario, Persona, Rol, Sexo


class RegistroTests(TestCase):
    def setUp(self):
        self.sexo = Sexo.objects.create(descripcion="Prueba")

    def test_registro_crea_relaciones_y_rol(self):
        response = self.client.post(reverse("registro"), {
            "username": "alumno_prueba",
            "email": "alumno@example.com",
            "password1": "ClavePrueba2026!f",
            "password2": "ClavePrueba2026!f",
            "nombre": "Alumno",
            "apellido": "Ejemplo",
            "documento": "1000012345",
            "fecha_nacimiento": "2008-01-15",
            "direccion": "Calle de prueba 1",
            "telefono": "3001234567",
            "sexo": self.sexo.pk,
            "necesidades_especiales": "",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="alumno_prueba")
        perfil = PerfilUsuario.objects.get(user=user)
        self.assertTrue(perfil.roles.filter(nombre="ESTUDIANTE").exists())
        persona = Persona.objects.get(perfil_user=perfil)
        self.assertTrue(Estudiante.objects.filter(persona=persona).exists())

    def test_registro_invalido_no_crea_usuario(self):
        response = self.client.post(reverse("registro"), {
            "username": "sin_datos", "password1": "abc", "password2": "xyz"
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sin_datos").exists())


class PermisosYCrudTests(TestCase):
    def setUp(self):
        self.estudiante = User.objects.create_user("estudiante", password="clave-test")
        perfil = PerfilUsuario.objects.create(user=self.estudiante)
        perfil.roles.add(Rol.objects.create(nombre="ESTUDIANTE"))
        self.admin = User.objects.create_superuser("administrador", "admin@example.com", "clave-test")
        self.grado = Grado.objects.create(nombre="Décimo")

    def test_estudiante_no_accede_a_gestiones(self):
        self.client.force_login(self.estudiante)
        for nombre in ("admin_gestion_db", "admin_gestion_users",
                       "admin_gestion_academica", "gestion_acudientes_estudiantes"):
            with self.subTest(vista=nombre):
                response = self.client.get(reverse(nombre))
                self.assertNotEqual(response.status_code, 200)

    def test_admin_puede_consultar_gestion_db(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_gestion_db"))
        self.assertEqual(response.status_code, 200)

    def test_eliminacion_por_get_no_modifica_datos(self):
        self.client.force_login(self.admin)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_estudiante_no_puede_eliminar(self):
        self.client.force_login(self.estudiante)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.client.post(url)
        self.assertTrue(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_admin_elimina_por_post(self):
        self.client.force_login(self.admin)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_admin_crea_rol(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_gestion_db"), {
            "form": "roles", "nombre": "DOCENTE", "descripcion": "Rol de prueba"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Rol.objects.filter(nombre="DOCENTE").exists())


class CuestionarioTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("quiz_user", password="clave-test")
        self.client.force_login(self.usuario)

    @patch("Principal.views.generar_material", return_value=["Álgebra"])
    @patch("Principal.views.generar_quizes", return_value=[{
        "pregunta": "¿Cuánto es 2 + 2?", "A": "3", "B": "4",
        "C": "5", "D": "6", "respuesta_correcta": "B",
    }])
    def test_cuestionario_llama_generador_y_recomendador(self, generar, materiales):
        response = self.client.post(reverse("test"), {"materia": "Matemáticas"})
        self.assertEqual(response.status_code, 200)
        generar.assert_called_once_with("Matemáticas", 1)
        materiales.assert_called_once()
        self.assertEqual(response.context["materiales_recomendados"], ["Álgebra"])
