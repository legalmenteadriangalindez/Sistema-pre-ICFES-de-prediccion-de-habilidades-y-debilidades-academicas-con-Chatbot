"""Pruebas del modo público gratuito con protección de datos y sin costes."""
import io
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from Principal.demo_views import demo_publica
from Principal.middleware_demo import BloqueoDemoMiddleware


@override_settings(DEMO_MODE=True, DEBUG=False)
class DemoGratuitaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = BloqueoDemoMiddleware(lambda _request: HttpResponse("OK"))

    def resolver(self, request, nombre):
        request.resolver_match = SimpleNamespace(url_name=nombre)
        return self.middleware.process_view(request, lambda r: None, (), {})

    def test_portada_publica_no_expone_datos(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        respuesta = demo_publica(request)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"datos ficticios", respuesta.content)
        self.assertIn(b"30", respuesta.content)

    def test_registro_nuevos_datos_y_admin_bloqueados(self):
        for ruta, nombre in [
            ("/registro/", "registro"),
            ("/gestion/reportes/", "admin_reportes_academicos"),
            ("/gestion/matriculas/importar/", "cargar_matriculas"),
        ]:
            respuesta = self.resolver(self.factory.post(ruta, {}), nombre)
            self.assertEqual(respuesta.status_code, 403)
        admin = self.resolver(self.factory.get("/admin/"), "index")
        self.assertEqual(admin.status_code, 404)

    def test_documentos_prohibidos_en_demo(self):
        archivo = SimpleUploadedFile("datos.pdf", b"%PDF-test")
        peticion = self.factory.post("/home/", {"archivo": archivo})
        self.assertEqual(self.resolver(peticion, "home").status_code, 403)

    def test_cuestionario_sintetico_permitido(self):
        peticion = self.factory.post("/simulacros/", {"accion": "iniciar"})
        self.assertIsNone(self.resolver(peticion, "simulacros"))

    @patch.dict("os.environ", {
        "PREICFES_DEMO_PASSWORD": "Clave-Ficticia-Larga-De-Render-2026!"
    })
    def test_crea_alumnos_ficticios_sin_superusuario_ni_clave_en_logs(self):
        salida = io.StringIO()
        call_command("crear_usuarios_prueba", stdout=salida)
        usuarios = get_user_model().objects
        self.assertTrue(usuarios.filter(username="estudiante_ana").exists())
        self.assertTrue(usuarios.filter(username="docente_demo").exists())
        self.assertTrue(usuarios.filter(username="admin_demo").exists())
        administrador = usuarios.get(username="admin_demo")
        self.assertFalse(administrador.is_superuser)
        self.assertFalse(administrador.is_staff)
        self.assertFalse(usuarios.filter(is_superuser=True).exists())
        self.assertNotIn("Clave-Ficticia", salida.getvalue())


    def test_administracion_local_visible_pero_solo_lectura(self):
        lectura = self.factory.get("/admin_gestion_users/")
        self.assertIsNone(self.resolver(lectura, "admin_gestion_users"))
        edicion = self.factory.post("/admin_gestion_users/", {"form": "usuarios"})
        respuesta = self.resolver(edicion, "admin_gestion_users")
        self.assertEqual(respuesta.status_code, 403)

    def test_contrasenas_compartidas_no_se_pueden_cambiar_desde_web(self):
        petición = self.factory.post(
            "/accounts/password_change/", {"old_password": "X"}
        )
        respuesta = self.resolver(petición, "password_change")
        self.assertEqual(respuesta.status_code, 403)

    @patch.dict("os.environ", {
        "PREICFES_DEMO_PASSWORD": "Clave-Ficticia-Larga-De-Render-2026!"
    })
    def test_tablero_estudiante_usa_home_original_sin_chatbot(self):
        call_command("crear_usuarios_prueba", stdout=io.StringIO())
        user = get_user_model().objects.get(username="estudiante_ana")
        self.client.force_login(user)

        with patch(
            "Principal.view_modules.chatbot.chatbotManager", None
        ):
            respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "home.html")
        self.assertContains(respuesta, "TU ESPACIO DE APRENDIZAJE")
        self.assertContains(respuesta, "IA no disponible")
        self.assertContains(respuesta, "Evaluaciones realizadas")
        self.assertNotContains(respuesta, 'id="chat-prompt"')
        self.assertEqual(self.client.post("/").status_code, 403)

    @patch.dict("os.environ", {
        "PREICFES_DEMO_PASSWORD": "Clave-Ficticia-Larga-De-Render-2026!"
    })
    def test_cuestionarios_locales_funcionan_sin_ollama(self):
        call_command("crear_usuarios_prueba", stdout=io.StringIO())
        user = get_user_model().objects.get(username="estudiante_ana")
        self.client.force_login(user)

        respuesta = self.client.post("/testDeVocacion/", {
            "materia": "Matematicas",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ecuaciones lineales")
        preguntas = self.client.session.get("prueba_materia_preguntas")
        self.assertEqual(len(preguntas), 2)
        self.assertEqual(preguntas[0]["respuesta_correcta"], "B")

        resultado = self.client.post("/testDeVocacion/", {
            "verificar_cuestionario": "1",
            "respuesta_0": "B",
            "respuesta_1": "C",
        })
        self.assertEqual(resultado.status_code, 200)
        self.assertContains(resultado, "2 de 2")
