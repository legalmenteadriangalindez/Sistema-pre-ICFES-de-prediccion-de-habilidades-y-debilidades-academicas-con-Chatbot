"""Pruebas del modo público gratuito con protección de datos y sin costes."""
import io
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
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
        respuesta = demo_publica(self.factory.get("/"))
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
        self.assertFalse(usuarios.filter(username="admin_demo").exists())
        self.assertFalse(usuarios.filter(is_superuser=True).exists())
        self.assertNotIn("Clave-Ficticia", salida.getvalue())
