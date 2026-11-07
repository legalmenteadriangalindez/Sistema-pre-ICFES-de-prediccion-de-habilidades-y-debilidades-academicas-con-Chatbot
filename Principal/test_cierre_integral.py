"""Pruebas de extremo a extremo Django: sesión, persistencia, permisos y privacidad.

Usan una base de test temporal. La IA externa se sustituye por un doble:
su comportamiento REAL se audita por separado con 'auditar_cierre --ollama'.
"""
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from Principal.models import Estudiante, IntentoEvaluacion, PerfilUsuario, Persona, RespuestaEvaluacion, Rol, Sexo


class CierreFuncionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sexo = Sexo.objects.create(descripcion="Prueba cierre")
        cls.estudiantes = []
        for i in range(2):
            usuario = User.objects.create_user(
                username=f"cierre_estudiante_{i}", password="PruebaCierre!2026"
            )
            perfil = PerfilUsuario.objects.create(user=usuario)
            rol, _ = Rol.objects.get_or_create(nombre="ESTUDIANTE")
            perfil.roles.add(rol)
            persona = Persona.objects.create(
                perfil_user=perfil, nombre=f"Alumno{i}", apellido="Prueba",
                documento=f"CIERRE-{i}", fecha_nacimiento=date(2008, 1, 1),
                direccion="Solo test", telefono="0000000000", sexo=sexo,
            )
            cls.estudiantes.append((usuario, Estudiante.objects.create(persona=persona)))
        cls.admin = User.objects.create_superuser(
            "cierre_admin", "cierre-admin@example.test", "PruebaCierre!2026"
        )
        cls.docente = User.objects.create_user("cierre_docente", password="PruebaCierre!2026")
        cls.acudiente = User.objects.create_user("cierre_acudiente", password="PruebaCierre!2026")
        for usuario, nombre in ((cls.docente, "DOCENTE"), (cls.acudiente, "ACUDIENTE")):
            perfil = PerfilUsuario.objects.create(user=usuario)
            rol, _ = Rol.objects.get_or_create(nombre=nombre)
            perfil.roles.add(rol)

    @staticmethod
    def bot_falso():
        bot = MagicMock()
        bot.memory_manager.get_user_chats.return_value = []
        bot.memory_manager.get_cognitive_profile.return_value = {}
        bot.get_conversation_history.return_value = []
        bot.chat.side_effect = [
            {"success": True, "response": "Primer turno", "chat_id": "cierre-hilo"},
            {"success": True, "response": "Segundo turno", "chat_id": "cierre-hilo"},
        ]
        return bot

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_conversacion_recarga_y_continuidad_de_hilo(self, manager):
        manager.return_value = bot = self.bot_falso()
        self.client.force_login(self.estudiantes[0][0])
        url = reverse("home")
        primera = self.client.post(url, {"prompt": "Primer mensaje"})
        self.assertEqual(primera.status_code, 200)
        self.assertEqual(self.client.session["chat_id_actual"], "cierre-hilo")
        recarga = self.client.get(url)
        self.assertEqual(recarga.status_code, 200)
        self.assertEqual(recarga.context["chat_id"], "cierre-hilo")
        segunda = self.client.post(url, {"prompt": "Segundo mensaje"})
        self.assertEqual(segunda.context["chat_id"], "cierre-hilo")
        self.assertEqual(bot.chat.call_count, 2)
        self.assertEqual(bot.chat.call_args_list[1].kwargs["chat_id"], "cierre-hilo")

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_pdf_real_se_guarda_privado_sin_publicarse(self, manager):
        manager.return_value = self.bot_falso()
        with tempfile.TemporaryDirectory() as carpeta:
            privado = Path(carpeta) / "privado"
            publico = Path(carpeta) / "publico"
            with override_settings(PRIVATE_UPLOAD_ROOT=privado, MEDIA_ROOT=publico):
                self.client.force_login(self.estudiantes[0][0])
                archivo = SimpleUploadedFile(
                    "guia.pdf", b"%PDF-1.4\n1 0 obj\n",
                    content_type="application/pdf",
                )
                respuesta = self.client.post(reverse("home"), {
                    "prompt": "Ayudame a estudiar", "archivo": archivo,
                })
                self.assertEqual(respuesta.status_code, 200)
                guardados = list((privado / str(self.estudiantes[0][0].pk) / "pdfs").glob("*.pdf"))
                self.assertEqual(len(guardados), 1)
                self.assertFalse((publico / "pdfs").exists())
                self.assertEqual(self.client.get("/media/" + guardados[0].name).status_code, 404)

    @patch("Principal.services.tutor_chat_actions.procesar_audio")
    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_audio_valido_llega_al_transcriptor_con_usuario_actual(self, manager, procesar):
        manager.return_value = self.bot_falso()
        procesar.return_value = ("Audio de prueba", "/ruta/privada/audio.wav")
        self.client.force_login(self.estudiantes[0][0])
        wav = b"RIFF" + (40).to_bytes(4, "little") + b"WAVEfmt " + b"\x00" * 32
        respuesta = self.client.post(reverse("home"), {
            "audio": SimpleUploadedFile("voz.wav", wav, content_type="audio/wav"),
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["audio_usuario"], "Audio de prueba")
        self.assertEqual(procesar.call_args.kwargs["user_id"], self.estudiantes[0][0].pk)

    def test_ingles_generar_calificar_historial_y_sin_reenvio(self):
        alumno, estudiante = self.estudiantes[0]
        self.client.force_login(alumno)
        url = reverse("test")
        generado = self.client.post(url, {"materia": "Ingles"})
        self.assertEqual(generado.status_code, 200)
        self.assertEqual(len(generado.context["preguntas_ingles"]), 10)
        self.assertNotIn("respuesta_correcta", generado.context["preguntas_ingles"][0])
        preguntas = self.client.session["prueba_ingles_preguntas"]
        respuestas = {f"respuesta_{p['id']}": p["respuesta_correcta"] for p in preguntas}
        calificado = self.client.post(url, {"verificar_ingles": "1", **respuestas})
        self.assertEqual(calificado.status_code, 200)
        self.assertEqual(calificado.context["resultado_ingles"]["porcentaje"], 100)
        intento = IntentoEvaluacion.objects.get(estudiante=estudiante)
        self.assertEqual(intento.aciertos, 10)
        self.assertEqual(RespuestaEvaluacion.objects.filter(intento=intento).count(), 10)
        self.assertTrue(RespuestaEvaluacion.objects.filter(intento=intento, explicacion__isnull=False).exists())
        self.assertEqual(self.client.post(url, {"verificar_ingles": "1", **respuestas}).context["error_prueba"],
                         "La evaluación expiró o ya fue calificada. Genera una nueva prueba.")
        self.assertEqual(IntentoEvaluacion.objects.count(), 1)
        historial = self.client.get(reverse("historial_academico"))
        self.assertEqual(historial.status_code, 200)
        self.assertEqual(historial.context["total_intentos"], 1)
        self.client.force_login(self.estudiantes[1][0])
        otro_historial = self.client.get(reverse("historial_academico"))
        self.assertEqual(otro_historial.context["total_intentos"], 0)

    def test_simulacro_ampliado_claves_privadas_y_resultado(self):
        alumno, estudiante = self.estudiantes[0]
        self.client.force_login(alumno)
        url = reverse("simulacros")
        iniciado = self.client.post(url, {"accion": "iniciar", "materia": "Integral ampliado"})
        self.assertEqual(iniciado.status_code, 200)
        self.assertEqual(len(iniciado.context["preguntas"]), 50)
        self.assertTrue(all("correcta" not in p and "explicacion" not in p
                            for p in iniciado.context["preguntas"]))
        preguntas = self.client.session["simulacro_activo"]["preguntas"]
        respuesta = {f"respuesta_{p['id']}": p["correcta"] for p in preguntas}
        finalizado = self.client.post(url, {"accion": "finalizar", **respuesta})
        self.assertEqual(finalizado.status_code, 200)
        self.assertEqual(finalizado.context["resultado"]["aciertos"], 50)
        self.assertEqual(IntentoEvaluacion.objects.filter(estudiante=estudiante).count(), 1)
        self.assertEqual(RespuestaEvaluacion.objects.filter(intento__estudiante=estudiante).count(), 50)
        self.assertEqual(self.client.post(url, {"accion": "finalizar"}).status_code, 400)

    def test_matriz_roles_y_exportacion_privada(self):
        for rol, usuario, panel in (
            ("ADMIN", self.admin, "admin_gestion_users"),
            ("DOCENTE", self.docente, "panel_docente"),
            ("ACUDIENTE", self.acudiente, "acudiente"),
        ):
            with self.subTest(rol=rol):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(reverse(panel)).status_code, 200)
        self.client.force_login(self.estudiantes[0][0])
        self.assertNotEqual(self.client.get(reverse("admin_gestion_users")).status_code, 200)
        self.assertEqual(self.client.get(reverse("panel_docente")).status_code, 403)
        self.assertEqual(self.client.get(reverse("acudiente")).status_code, 403)
        exportacion = self.client.get(reverse("exportar_mis_datos"))
        self.assertEqual(exportacion.status_code, 200)
        self.assertIn("no-store", exportacion["Cache-Control"])
        datos = json.loads(exportacion.content)
        self.assertEqual(datos["cuenta"]["usuario"], "cierre_estudiante_0")
        serializado = json.dumps(datos, ensure_ascii=False)
        self.assertNotIn("CIERRE-1", serializado)
        self.assertNotIn("password", serializado.lower())

    def test_auditoria_real_de_base_sin_modelo_ni_entrenamiento(self):
        from io import StringIO
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as carpeta:
            with override_settings(PREDICCION_MODELO_PATH=Path(carpeta) / "modelo.json"):
                salida = StringIO()
                call_command("auditar_cierre", stdout=salida)
                datos = json.loads(salida.getvalue())
                self.assertEqual(datos["operacion"], "solo_lectura")
                self.assertFalse(datos["prediccion"]["suficiente_para_intentar"])
                self.assertFalse(datos["prediccion"]["modelo_validado_disponible"])
                self.assertEqual(datos["ollama"]["estado"], "no_comprobado")
                self.assertFalse((Path(carpeta) / "modelo.json").exists())
