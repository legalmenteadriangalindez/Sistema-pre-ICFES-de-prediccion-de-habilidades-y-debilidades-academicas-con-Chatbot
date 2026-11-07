"""Regresiones de adjuntos procesados y preparación operativa del servidor."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from Principal.services.documentos_tutor import extraer_texto_pdf
from Principal.services.tutor_chat_actions import procesar_post_chat


def pdf_de_prueba():
    return SimpleUploadedFile(
        "ejercicio.pdf", b"%PDF-1.4\n1 0 obj\n",
        content_type="application/pdf",
    )


def audio_de_prueba():
    return SimpleUploadedFile(
        "consulta.wav", b"RIFF0000WAVE" + b"0000",
        content_type="audio/wav",
    )


class EstadoOperativoTests(TestCase):
    def test_healthz_y_readyz_sin_datos_privados(self):
        vida = self.client.get(reverse("healthz"))
        listo = self.client.get(reverse("readyz"))
        self.assertEqual(vida.status_code, 200)
        self.assertEqual(listo.status_code, 200)
        self.assertEqual(vida.json(), {"status": "alive"})
        self.assertEqual(listo.json(), {"status": "ready"})
        self.assertEqual(vida["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate, private")


class ExtraerDocumentoTests(TestCase):
    @patch("pypdf.PdfReader")
    def test_extrae_texto_y_restaura_cursor(self, lector):
        archivo = pdf_de_prueba()
        lector.return_value.is_encrypted = False
        pagina = MagicMock()
        pagina.extract_text.return_value = "La fotosíntesis transforma energía solar en química."
        lector.return_value.pages = [pagina]
        archivo.seek(3)
        texto = extraer_texto_pdf(archivo)
        self.assertIn("fotosíntesis", texto)
        self.assertEqual(archivo.tell(), 3)

    @patch("pypdf.PdfReader")
    def test_rechaza_pdf_escaneado_sin_texto(self, lector):
        archivo = pdf_de_prueba()
        lector.return_value.is_encrypted = False
        pagina = MagicMock()
        pagina.extract_text.return_value = ""
        lector.return_value.pages = [pagina]
        with self.assertRaisesMessage(ValidationError, "OCR"):
            extraer_texto_pdf(archivo)

    @patch("pypdf.PdfReader")
    def test_rechaza_pdf_extenso(self, lector):
        lector.return_value.is_encrypted = False
        lector.return_value.pages = [MagicMock()] * 26
        with self.assertRaisesMessage(ValidationError, "25 páginas"):
            extraer_texto_pdf(pdf_de_prueba())


class ChatAdjuntosTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.bot = MagicMock()
        self.bot.chat.return_value = {
            "success": True, "response": "Guía de repaso",
            "chat_id": "hilo-pruebas",
        }
        self.bot.get_conversation_history.return_value = []
        self.bot.memory_manager.get_user_chats.return_value = []
        self.bot.memory_manager.get_cognitive_profile.return_value = []
        self.usuario = SimpleNamespace(pk=51, id=51, is_authenticated=True)

    def solicitud(self, datos):
        request = self.factory.post("/", datos)
        request.user = self.usuario
        request.session = {}
        return request

    @patch("Principal.services.tutor_chat_actions.sincronizar_perfil_academico")
    @patch("Principal.services.tutor_chat_actions.extraer_texto_pdf")
    @patch("Principal.services.tutor_chat_actions.guardar_PDFs")
    def test_pdf_alimenta_contexto_y_se_mantiene_privado(
        self, guardar, extraer, _sincronizar
    ):
        guardar.return_value = "/privado/51/pdf.pdf"
        extraer.return_value = "La teoría matemática explica la suma de enteros positivos."
        req = self.solicitud({
            "archivo": pdf_de_prueba(), "prompt": "Resume el documento adjunto"
        })
        salida = procesar_post_chat(
            req, self.bot, {}, None, "default",
            lambda _req, _template, contexto: contexto,
        )
        self.assertTrue(salida["pdf_analizado"])
        self.assertEqual(salida["response"], "Guía de repaso")
        parametros = self.bot.chat.call_args.kwargs
        self.assertIn("La teoría matemática", parametros["academic_context"])
        self.assertIn("MATERIAL ADJUNTO", parametros["academic_context"])
        self.assertNotIn("/privado/", parametros["academic_context"])
        guardar.assert_called_once()

    @patch("Principal.services.tutor_chat_actions.sincronizar_perfil_academico")
    @patch("Principal.services.tutor_chat_actions.procesar_audio")
    def test_audio_sin_texto_se_envia_al_tutor(self, procesar, _sincronizar):
        procesar.return_value = (
            "¿Cómo se obtiene el perímetro de un triángulo?",
            "/privado/voz.wav",
        )
        salida = procesar_post_chat(
            self.solicitud({"audio": audio_de_prueba()}),
            self.bot, {}, None, "default",
            lambda _req, _template, contexto: contexto,
        )
        self.assertEqual(salida["audio_usuario"], procesar.return_value[0])
        mensaje = self.bot.chat.call_args.args[0]
        self.assertIn("perímetro de un triángulo", mensaje)
        self.assertNotIn("/privado/", mensaje)

    @patch("Principal.services.tutor_chat_actions.procesar_audio")
    def test_audio_sin_transcripcion_no_finge_respuesta(self, procesar):
        procesar.return_value = ("", "/privado/vacio.wav")
        salida = procesar_post_chat(
            self.solicitud({"audio": audio_de_prueba()}),
            self.bot, {}, None, "default",
            lambda _req, _template, contexto: contexto,
        )
        self.assertIn("No se pudo transcribir", salida["chat_error"])
        self.bot.chat.assert_not_called()
