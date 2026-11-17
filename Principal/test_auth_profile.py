"""Pruebas de autenticación y edición del perfil propio."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Estudiante, PerfilUsuario, Persona, Rol, Sexo


class AutenticacionPerfilTests(TestCase):
    password = "ClaveSegura!2026"

    def setUp(self):
        self.sexo = Sexo.objects.create(descripcion="Prefiero no indicar")
        self.usuario, self.persona = self._crear_usuario(
            "alumno_fase2", "alumno.fase2@example.test", "ESTUDIANTE", "F2-001"
        )
        self.otro_usuario, self.otra_persona = self._crear_usuario(
            "otro_fase2", "otro.fase2@example.test", "ESTUDIANTE", "F2-002"
        )

    def _crear_usuario(self, username, email, rol, documento):
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=self.password,
            first_name="Nombre",
            last_name="Prueba",
        )
        perfil = PerfilUsuario.objects.create(user=user)
        rol_obj, _ = Rol.objects.get_or_create(nombre=rol)\n        perfil.roles.add(rol_obj)
        persona = Persona.objects.create(
            perfil_user=perfil,
            nombre="Nombre",
            apellido="Prueba",
            documento=documento,
            fecha_nacimiento=date(2008, 1, 1),
            direccion="Carrera 1 # 2-3",
            telefono="3000000000",
            sexo=self.sexo,
        )
        Estudiante.objects.create(
            persona=persona,
            necesidades_especiales="Ninguna",
        )
        return user, persona

    def _payload(self, user, persona):
        return {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "nombre": persona.nombre,
            "apellido": persona.apellido,
            "documento": persona.documento,
            "fecha_nacimiento": persona.fecha_nacimiento.isoformat(),
            "direccion": persona.direccion,
            "telefono": persona.telefono,
            "sexo": str(persona.sexo_id),
            "necesidades_especiales": "Apoyo actualizado",
        }

    def test_correo_sin_cambios_es_valido(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse("perfil_editar"),
            self._payload(self.usuario, self.persona),
        )
        self.assertRedirects(response, reverse("perfil"))
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "alumno.fase2@example.test")

    def test_correo_duplicado_no_modifica_la_cuenta(self):
        self.client.force_login(self.usuario)
        datos = self._payload(self.usuario, self.persona)
        datos["email"] = self.otro_usuario.email

        response = self.client.post(reverse("perfil_editar"), datos)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "user_form",
            "email",
            "Este correo electrónico ya está registrado.",
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "alumno.fase2@example.test")

    def test_cambio_de_contrasena_es_independiente_y_funciona(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("perfil_editar"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="old_password"')
        self.assertNotContains(response, 'name="new_password1"')

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.password,
                "new_password1": "NuevaClave!2026",
                "new_password2": "NuevaClave!2026",
            },
        )
        self.assertRedirects(response, reverse("password_change_done"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NuevaClave!2026"))

    def test_roles_autenticados_acceden_a_su_edicion(self):
        for role in ("ESTUDIANTE", "DOCENTE", "ACUDIENTE"):
            user = get_user_model().objects.create_user(
                username=f"rol_{role.lower()}",
                password=self.password,
            )
            perfil = PerfilUsuario.objects.create(user=user)
            perfil.roles.add(Rol.objects.create(nombre=role))

            self.client.force_login(user)
            response = self.client.get(reverse("perfil_editar"))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'name="username"')
            self.assertContains(response, user.username)

    def test_usuario_anonimo_no_puede_editar_perfil(self):
        response = self.client.get(reverse("perfil_editar"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('perfil_editar')}",
            fetch_redirect_response=False,
        )

    def test_edicion_no_permite_acceso_cruzado_entre_usuarios(self):
        self.client.force_login(self.usuario)
        datos = self._payload(self.usuario, self.persona)
        datos.update(
            {
                "nombre": "Cambio propio",
                "necesidades_especiales": "Solo pertenece al primer usuario",
                "persona_id": str(self.otra_persona.pk),
                "usuario_id": str(self.otro_usuario.pk),
            }
        )

        response = self.client.post(reverse("perfil_editar"), datos)

        self.assertRedirects(response, reverse("perfil"))
        self.persona.refresh_from_db()
        self.otra_persona.refresh_from_db()
        self.otro_usuario.refresh_from_db()
        self.assertEqual(self.persona.nombre, "Cambio propio")
        self.assertEqual(self.otra_persona.nombre, "Nombre")
        self.assertEqual(self.otro_usuario.email, "otro.fase2@example.test")
