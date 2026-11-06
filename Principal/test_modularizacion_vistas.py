"""Contrato de fachadas Django: preservar rutas, permisos y puntos de mock históricos.

Pruebas sin Ollama ni datos personales. La batería preexistente verifica el
comportamiento completo de registro, chat, cuestionarios y módulos académicos.
"""
import inspect
from pathlib import Path

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import resolve, reverse

from Principal import management_views, portal_academico, views
from Principal.view_modules import (
    admin_catalogos, admin_docentes, admin_matriculas, admin_usuarios,
    autenticacion, chatbot, cuestionarios, docentes, estudiantes, perfiles,
    seguimiento, selectores, vocacional,
)


class ModularizacionVistasTests(TestCase):
    def test_rutas_existentes_siguen_vinculadas_a_los_nombres_publicos(self):
        publicas = {
            "home": views.home,
            "test": views.test,
            "registro": views.registro,
            "verificar_correo": views.verificar_correo,
            "perfil": views.perfil,
            "configuraciones": views.configuraciones,
            "recomendaciones": views.recomendaciones,
            "actividadesUsuario": views.actividadesUsuario,
            "salir": views.salir,
            "orientacion_vocacional": portal_academico.orientacion_vocacional,
            "plan_semanal": portal_academico.plan_estudio,
            "diagnostico_academico": portal_academico.diagnostico_academico,
            "panel_docente": portal_academico.panel_docente,
            "acudiente": portal_academico.panel_acudiente,
            "comparadorDeCarreras": portal_academico.comparador_carreras,
            "admin_asignaciones_docentes": views.gestion_docentes,
            "admin_gestion_users": views.gestion_users,
            "admin_gestion_academica": views.gestion_academica,
            "admin_gestion_db": views.gestion_db,
            "gestion_acudientes_estudiantes": views.gestion_acudientes_estudiantes,
        }
        for nombre, funcion in publicas.items():
            with self.subTest(ruta=nombre):
                self.assertIs(resolve(reverse(nombre)).func, funcion)
        self.assertIs(
            resolve(reverse("verificar_correo", args=["abc"])).func,
            views.verificar_correo,
        )

    def test_urls_administrativas_de_eliminacion_siguen_protegidas_por_post(self):
        rutas = {
            "eliminar_admin_gestion_users": views.eliminar_gestion_users,
            "eliminar_admin_gestion_db": views.eliminar_admin_gestion_db,
            "eliminar_admin_gestion_academico": views.eliminar_gestion_academica,
            "eliminar_gestion_acudientes_estudiantes": views.eliminar_gestion_acudientes_estudiantes,
        }
        for nombre, funcion in rutas.items():
            with self.subTest(ruta=nombre):
                self.assertIs(
                    resolve(reverse(nombre, args=["usuarios", 1])).func, funcion
                )
                respuesta = self.client.get(reverse(nombre, args=["usuarios", 1]))
                self.assertIn(respuesta.status_code, (302, 403, 405))
                self.assertNotEqual(respuesta.status_code, 200)

    def test_compatibilidad_de_dependencias_empleadas_en_mocks(self):
        self.assertIn("render_func", inspect.signature(chatbot.home).parameters)
        self.assertIn("enviar_verificacion_func", inspect.signature(autenticacion.registro).parameters)
        self.assertIn("generar_quizes_func", inspect.signature(cuestionarios.test).parameters)
        self.assertIn("generar_material_func", inspect.signature(cuestionarios.test).parameters)
        self.assertIs(
            views.chatbotManager, chatbot.chatbotManager
        )

    def test_los_helpers_compartidos_son_identicos_en_todas_las_fachadas(self):
        self.assertIs(management_views.es_gestor, selectores.es_gestor)
        self.assertIs(portal_academico._estudiante, selectores._estudiante)
        self.assertIs(portal_academico._tiene_rol, selectores._tiene_rol)
        self.assertIs(portal_academico.matriculas_permitidas_docente,
                      docentes.matriculas_permitidas_docente)
        self.assertIs(views.gestion_users, admin_usuarios.gestion_users)
        self.assertIs(views.gestion_docentes, admin_docentes.gestion_docentes)
        self.assertIs(views.gestion_academica, admin_catalogos.gestion_academica)
        self.assertIs(views.gestion_acudientes_estudiantes,
                      admin_matriculas.gestion_acudientes_estudiantes)
        self.assertIs(views.perfil, perfiles.perfil)
        self.assertIs(views.actividadesUsuario, estudiantes.actividadesUsuario)
        self.assertIs(portal_academico.plan_estudio, seguimiento.plan_estudio)
        self.assertIs(views.comparadorDeCarreras, vocacional.comparadorDeCarreras)

    def test_rutas_privadas_siguen_exigiendo_autenticacion(self):
        nombres = (
            "home", "test", "perfil", "actividadesUsuario",
            "plan_semanal", "diagnostico_academico",
            "orientacion_vocacional", "panel_docente",
            "acudiente", "admin_gestion_users", "admin_gestion_db",
            "admin_gestion_academica", "admin_asignaciones_docentes",
        )
        for nombre in nombres:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("login", respuesta["Location"])

    def test_fachadas_son_delgadas_y_modulos_no_importan_la_fachada(self):
        base = Path(__file__).parent
        limites = {
            "views.py": 90,
            "portal_academico.py": 50,
            "management_views.py": 55,
        }
        for archivo, max_lineas in limites.items():
            with self.subTest(archivo=archivo):
                self.assertLess(
                    len((base / archivo).read_text(encoding="utf-8").splitlines()),
                    max_lineas,
                )
        for archivo in (base / "view_modules").glob("*.py"):
            with self.subTest(modulo=archivo.name):
                texto = archivo.read_text(encoding="utf-8")
                self.assertNotIn("from Principal import views", texto)
                self.assertNotIn("from Principal.management_views import", texto)
                self.assertNotIn("from Principal.portal_academico import", texto)
                self.assertLess(len(texto.splitlines()), 240)
