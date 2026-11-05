"""Pruebas del comando de preparación local de datos ficticios."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .models import Acudiente, Estudiante, EstudianteAcudiente, Matricula, Persona, PerfilUsuario


class CrearUsuariosPruebaTests(TestCase):
    @override_settings(DEBUG=True)
    def test_crea_roles_personas_estudiantes_y_matriculas_sin_duplicados(self):
        call_command("crear_usuarios_prueba", verbosity=0)
        User = get_user_model()
        self.assertEqual(User.objects.count(), 5)
        self.assertTrue(User.objects.get(username="admin_demo").is_superuser)
        self.assertTrue(User.objects.get(username="admin_demo").is_staff)
        self.assertEqual(PerfilUsuario.objects.count(), 5)
        self.assertEqual(Persona.objects.count(), 5)
        self.assertEqual(Estudiante.objects.count(), 2)
        self.assertEqual(Acudiente.objects.count(), 1)
        self.assertEqual(Matricula.objects.count(), 2)
        self.assertEqual(EstudianteAcudiente.objects.count(), 2)
        self.assertTrue(User.objects.get(username="estudiante_ana").is_active)
        self.assertTrue(User.objects.get(username="estudiante_ana").check_password("PreICFES2026!Demo"))
        self.assertTrue(PerfilUsuario.objects.get(user__username="docente_demo").roles.filter(nombre="DOCENTE").exists())

        call_command("crear_usuarios_prueba", verbosity=0)
        self.assertEqual(User.objects.count(), 5)
        self.assertEqual(Matricula.objects.count(), 2)
        self.assertEqual(EstudianteAcudiente.objects.count(), 2)

    @override_settings(DEBUG=True)
    def test_reseteo_explicitamente_solicitado(self):
        call_command("crear_usuarios_prueba", verbosity=0)
        User = get_user_model()
        user = User.objects.get(username="estudiante_ana")
        user.set_password("OtraClaveDePrueba!2026")
        user.save()
        call_command("crear_usuarios_prueba", verbosity=0)
        user.refresh_from_db()
        self.assertTrue(user.check_password("OtraClaveDePrueba!2026"))
        call_command("crear_usuarios_prueba", resetear_claves=True, verbosity=0)
        user.refresh_from_db()
        self.assertTrue(user.check_password("PreICFES2026!Demo"))

    @override_settings(DEBUG=False)
    def test_no_permite_crear_cuentas_de_prueba_en_produccion(self):
        with self.assertRaises(CommandError):
            call_command("crear_usuarios_prueba", verbosity=0)
