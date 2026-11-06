"""Pruebas de alertas reutilizables y compatibilidad del panel administrativo."""
from pathlib import Path

from django.contrib.messages import ERROR, SUCCESS, WARNING
from django.contrib.messages.storage.base import Message
from django.template.loader import get_template, render_to_string
from django.test import SimpleTestCase


class NotificacionesUiTests(SimpleTestCase):
    def test_sin_mensajes_permanece_oculto(self):
        html = render_to_string("components/notifications.html", {"messages": []})
        self.assertIn('id="app-notifications"', html)
        self.assertIn("hidden", html)

    def test_mensajes_django_conservan_severidad_y_escapan_html(self):
        html = render_to_string("components/notifications.html", {
            "messages": [
                Message(ERROR, '<script>alert("x")</script>'),
                Message(WARNING, "Comprueba la información"),
                Message(SUCCESS, "Guardado"),
            ],
        })
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertEqual(html.count('role="alert"'), 2)
        self.assertEqual(html.count('role="status"'), 1)
        self.assertEqual(html.count("data-notice-dismiss"), 3)
        self.assertNotIn('class="app-notifications" hidden', html)

    def test_template_base_carga_un_solo_controlador_de_preferencias(self):
        shell = Path(get_template("app_shell.html").origin.name).read_text(encoding="utf-8")
        self.assertEqual(shell.count("js/ui-polish.js"), 1)
        self.assertNotIn("js/script.js", shell)
        self.assertEqual(shell.count("js/notifications.js"), 1)
        self.assertEqual(shell.count('components/notifications.html'), 1)
        self.assertLess(shell.index("css/portal-academico.css"), shell.index("css/notifications.css"))
        self.assertLess(shell.index("css/notifications.css"), shell.index("{% block extra_head %}"))

    def test_plan_semanal_no_duplica_mensajes_globales(self):
        plan = Path(get_template("PlanSemanal.html").origin.name).read_text(encoding="utf-8")
        self.assertNotIn("for mensaje in messages", plan)
        self.assertNotIn("for message in messages", plan)

    def test_administracion_legible_sin_cambiar_formularios_ni_rutas(self):
        template = get_template("admin_gestion_user.html")
        content = Path(template.origin.name).read_text(encoding="utf-8")
        self.assertGreaterEqual(len(content.splitlines()), 100)
        self.assertIn('id="users-table"', content.replace('table_id="users-table"', 'id="users-table"'))
        for original in (
            'name="form" value="usuarios"',
            'name="form" value="personas"',
            '{% csrf_token %}',
            'components/table.html',
            'admin_gestion_academica',
            'gestion_acudientes_estudiantes',
            'admin_gestion_db',
        ):
            self.assertIn(original, content)
        self.assertNotIn('onclick=', content)
        self.assertNotIn('onsubmit=', content)
