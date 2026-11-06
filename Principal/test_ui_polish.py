"""Regresiones de los cambios de experiencia de usuario 2026.

Pruebas HTML: no requieren Ollama, red ni archivos personales.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class InterfazPulidaTests(TestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_superuser(
            username='gestor_visual', email='gestor_visual@example.test',
            password='PruebaSegura!2026'
        )
        self.estudiante = get_user_model().objects.create_user(
            username='alumno_visual', password='PruebaSegura!2026'
        )

    def test_administrador_ve_metricas_reales_y_controles(self):
        self.client.force_login(self.administrador)
        response = self.client.get(reverse('admin_gestion_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión administrativa')
        self.assertContains(response, 'gestor_visual')
        self.assertContains(response, 'id="user-search"')
        self.assertContains(response, 'id="role-filter"')
        self.assertContains(response, 'Usuarios')

    def test_estudiante_no_accede_al_panel_de_gestion(self):
        self.client.force_login(self.estudiante)
        response = self.client.get(reverse('admin_gestion_users'))
        self.assertIn(response.status_code, (302, 403))

    def test_preferencias_son_visuales_sin_interferir_con_cuenta(self):
        self.client.force_login(self.estudiante)
        response = self.client.get(reverse('configuraciones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-ui-preference="dark"')
        self.assertContains(response, 'data-ui-preference="text-size"')
        self.assertContains(response, 'data-ui-preference="reduce-motion"')
        self.assertContains(response, 'js/ui-polish.js')

    def test_admin_no_puede_desactivar_su_propia_cuenta(self):
        self.client.force_login(self.administrador)
        response = self.client.post(reverse('admin_gestion_users'), {
            'form': 'cambiar_estado', 'usuario_id': str(self.administrador.pk)
        })
        self.assertEqual(response.status_code, 200)
        self.administrador.refresh_from_db()
        self.assertTrue(self.administrador.is_active)

    def test_admin_no_se_elimina_desde_su_propio_panel(self):
        self.client.force_login(self.administrador)
        response = self.client.post(reverse('eliminar_admin_gestion_users',
                                            args=['usuarios', self.administrador.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(pk=self.administrador.pk).exists())
