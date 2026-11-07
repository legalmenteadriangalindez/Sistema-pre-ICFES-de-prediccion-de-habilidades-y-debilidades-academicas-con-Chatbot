"""Matriz de autorización por rol y regresiones de acceso a datos personales."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Principal.models import PerfilUsuario, Rol


class MatrizPermisosPorRolTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            "admin_matriz", "admin_matriz@example.test", "ClaveSegura2026!"
        )
        cls.usuarios = {}
        for nombre in ("ESTUDIANTE", "DOCENTE", "ACUDIENTE"):
            usuario = User.objects.create_user(
                "matriz_" + nombre.lower(),
                password="ClaveSegura2026!",
            )
            perfil = PerfilUsuario.objects.create(user=usuario)
            rol, _ = Rol.objects.get_or_create(nombre=nombre)
            perfil.roles.add(rol)
            cls.usuarios[nombre] = usuario

    def test_solo_administrador_consulta_gestion_usuarios(self):
        url = reverse("admin_gestion_users")
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        for usuario in self.usuarios.values():
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertNotEqual(self.client.get(url).status_code, 200)

    def test_docente_no_puede_ser_suplantado_por_otros_roles(self):
        url = reverse("panel_docente")
        for rol, usuario in self.usuarios.items():
            with self.subTest(rol=rol):
                self.client.force_login(usuario)
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200 if rol == "DOCENTE" else 403)

    def test_acudiente_no_puede_ser_suplantado_por_otros_roles(self):
        url = reverse("acudiente")
        for rol, usuario in self.usuarios.items():
            with self.subTest(rol=rol):
                self.client.force_login(usuario)
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200 if rol == "ACUDIENTE" else 403)

    def test_cuentas_sin_estudiante_no_ven_diagnostico_ni_recomendaciones(self):
        for usuario in self.usuarios.values():
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(reverse("diagnostico_academico")).status_code, 403)
                self.assertEqual(self.client.get(reverse("recomendaciones")).status_code, 403)

    def test_borrado_de_cuentas_solo_por_post_y_administrador(self):
        victima = self.usuarios["ESTUDIANTE"]
        url = reverse("eliminar_admin_gestion_users", args=["usuarios", victima.pk])
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(User.objects.filter(pk=victima.pk).exists())
        self.client.force_login(self.usuarios["DOCENTE"])
        self.assertNotEqual(self.client.post(url).status_code, 200)
        self.assertTrue(User.objects.filter(pk=victima.pk).exists())

    def test_anonymous_no_puede_consultar_portales(self):
        self.client.logout()
        for nombre in ("admin_gestion_users", "panel_docente", "acudiente", "diagnostico_academico"):
            with self.subTest(ruta=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 302)
