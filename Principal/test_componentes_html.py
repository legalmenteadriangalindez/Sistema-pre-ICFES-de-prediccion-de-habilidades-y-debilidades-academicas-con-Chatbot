"""Regresiones de componentes HTML sin cambiar los permisos ni la lógica existente."""
import re

from django import forms
from django.contrib.auth import get_user_model
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse


class FormularioDemostracion(forms.Form):
    nombre = forms.CharField(max_length=50)


class ComponentesHTMLTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin_componentes", email="admin-componentes@example.test",
            password="ClaveSegura!2026",
        )
        self.otro = get_user_model().objects.create_user(
            username="alumno_componentes", password="ClaveSegura!2026",
        )

    def test_avisos_escapan_texto_y_utilizan_roles_correctos(self):
        texto = '<img src=x onerror="alert(1)">'
        alerta = render_to_string("components/alert.html", {
            "tone": "warning", "message": texto,
        })
        self.assertIn('role="alert"', alerta)
        self.assertIn("ui-alert-warning", alerta)
        self.assertNotIn("<img", alerta)
        self.assertIn("&lt;img", alerta)
        exito = render_to_string("components/alert.html", {
            "tone": "success", "role": "status", "message": "Correcto",
        })
        self.assertIn('role="status"', exito)
        self.assertIn("ui-alert-success", exito)

    def test_tarjeta_y_metricas_conservan_estructura_html(self):
        tarjeta = render_to_string("components/info_card.html", {
            "title": "Seguridad de datos", "description": "Información propia",
            "action_url": "/privacidad/exportar/",
            "action_label": "Descargar", "role": "status",
        })
        self.assertIn('<section class="ui-card"', tarjeta)
        self.assertIn('role="status"', tarjeta)
        self.assertIn('href="/privacidad/exportar/"', tarjeta)
        metrica = render_to_string("components/metric_card.html", {
            "icon": "fas fa-users", "color": "blue",
            "label": "Usuarios", "value": 3,
        })
        self.assertIn('class="ui-card stat-card"', metrica)
        self.assertIn("<strong>3</strong>", metrica)
        item = render_to_string("components/metric_item.html", {
            "label": "Cumplimiento", "value": 80, "suffix": "%",
            "detail_prefix": "Mínimo ", "detail_value": 50,
        })
        self.assertIn("<strong>80%</strong>", item)
        self.assertIn("Mínimo 50", item)

    def test_campo_de_formulario_reutiliza_widget_errores_y_etiqueta(self):
        formulario = FormularioDemostracion(data={"nombre": ""})
        self.assertFalse(formulario.is_valid())
        campo = render_to_string("components/form_field.html", {
            "field": formulario["nombre"], "label_text": "Nombre completo",
        })
        self.assertIn('for="id_nombre"', campo)
        self.assertIn('name="nombre"', campo)
        self.assertIn('id="id_nombre"', campo)
        self.assertIn('invalid-feedback', campo)
        self.assertIn("Nombre completo", campo)

    def test_tablas_conservan_filas_y_columnas_de_la_administracion(self):
        request = RequestFactory().get(reverse("admin_gestion_users"))
        request.user = self.admin
        table = render_to_string("components/table.html", {
            "table_id": "users-table",
            "table_class": "table admin-table",
            "caption": "Cuentas registradas",
            "colspan": 6, "rows": [self.admin],
            "header_template": "components/tables/users_header.html",
            "row_template": "components/tables/user_row.html",
            "user": self.admin,
        }, request=request)
        self.assertIn('id="users-table"', table)
        self.assertIn("<th scope=\"col\">Acción</th>", table)
        self.assertIn("@admin_componentes", table)
        self.assertIn("Tu cuenta", table)
        self.assertEqual(table.count("<tr"), 2)
        empty = render_to_string("components/table.html", {
            "rows": [], "colspan": 3,
            "header_template": "components/tables/people_header.html",
            "row_template": "components/tables/person_row.html",
        })
        self.assertIn('colspan="3"', empty)
        self.assertIn("Sin registros disponibles", empty)

    def test_modal_reutilizable_preserva_token_y_parametro_de_formulario(self):
        request = RequestFactory().get("/")
        modal = render_to_string("components/form_modal.html", {
            "modal_id": "agregar_grado", "modal_title": "Agregar nuevo grado",
            "form": FormularioDemostracion(), "submit_value": "grados",
        }, request=request)
        self.assertIn('id="agregar_grado"', modal)
        self.assertIn('aria-labelledby="agregar_grado-title"', modal)
        self.assertIn('name="form" value="grados"', modal)
        self.assertIn('name="nombre"', modal)
        self.assertIn('name="csrfmiddlewaretoken"', modal)
        self.assertEqual(modal.count("<form"), 1)
        self.assertIn('data-bs-dismiss="modal"', modal)

    def test_pantalla_administrativa_conserva_tablas_filtros_y_acciones(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_gestion_users"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="users-table"')
        self.assertContains(response, 'id="user-search"')
        self.assertContains(response, 'id="role-filter"')
        self.assertContains(response, 'id="table-count"')
        self.assertContains(response, 'data-confirm="¿Eliminar el usuario alumno_componentes?')
        self.assertContains(response, 'name="form" value="asignar_rol"')
        self.assertContains(response, 'name="form" value="cambiar_estado"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_registro_mantiene_nombres_originales_de_campos(self):
        response = self.client.get(reverse("registro"))
        self.assertEqual(response.status_code, 200)
        for name in (
            "username", "email", "password1", "password2", "nombre",
            "apellido", "documento", "fecha_nacimiento", "sexo",
            "direccion", "telefono", "necesidades_especiales",
        ):
            self.assertContains(response, f'name="{name}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, 'for=""')

    def test_modales_de_gestion_academica_son_unicos_y_formularios_siguen(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_gestion_academica"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        ids = re.findall(r'class="modal fade" id="([^"]+)"', html)
        self.assertEqual(len(ids), 4)
        self.assertEqual(len(ids), len(set(ids)))
        for table_name in ("grados", "cursos", "anios", "materias"):
            self.assertIn(f'name="form" value="{table_name}"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_privacidad_y_prediccion_mantienen_tarjetas_y_enlaces(self):
        self.client.force_login(self.otro)
        privacidad = self.client.get(reverse("privacidad"))
        self.assertEqual(privacidad.status_code, 200)
        self.assertContains(privacidad, "Exportar mi información")
        self.assertContains(privacidad, reverse("exportar_mis_datos"))
        # Para la predicción se necesita estudiante; la tarjeta se comprueba
        # directamente con el contexto usado por esa vista.
        pagina = render_to_string("components/info_card.html", {
            "title": "Predicción aún no validada", "role": "status",
            "description": "Sin modelo validado", "action_url": "/diagnostico-academico/",
            "action_label": "Consultar mis resultados reales",
        })
        self.assertIn("Predicción aún no validada", pagina)

    def test_plantillas_modificadas_compilan_y_no_hay_eventos_inline(self):
        nombres = [
            "Registro.html", "admin_gestion_user.html", "PlanSemanal.html",
            "PanelDocente.html", "OrientacionVocacional.html",
            "AdminAsignacionesDocentes.html", "PrediccionAcademica.html",
            "Privacidad.html", "ValidacionPrediccion.html",
            "admin_gestion_academica.html", "gestion_estudiantes_acudientes.html",
            "actividadesUsuario.html", "components/alert.html",
            "components/info_card.html", "components/metric_card.html",
            "components/metric_item.html", "components/table.html",
            "components/form_field.html", "components/form_modal.html",
            "components/tables/user_row.html", "components/tables/person_row.html",
        ]
        for name in nombres:
            with self.subTest(plantilla=name):
                plantilla = get_template(name)
                self.assertIsNotNone(plantilla)
                source = open(plantilla.origin.name, encoding="utf-8").read()
                self.assertIsNone(re.search(
                    r"\bon(?:click|submit|change|input|load)\s*=", source, re.IGNORECASE
                ))
