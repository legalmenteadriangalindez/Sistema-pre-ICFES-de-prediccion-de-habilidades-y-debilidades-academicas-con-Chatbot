"""Regresiones de seguridad: archivos privados, permisos docentes, datos propios."""
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Actividad, ActividadAsignada, AnioLectivo, AsignacionDocenteCurso, Curso,
    Estudiante, Grado, IntentoEvaluacion, Matricula, Materia,
    NivelAprendizaje, PerfilUsuario, Persona, Rol, Sexo, Tema,
)
from .services.files import guardar_PDFs, guardar_audio, validar_audio, validar_pdf
from .services.privacidad import eliminar_directorios_de_cuenta


class ArchivosPrivadosTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.settings = override_settings(
            PRIVATE_UPLOAD_ROOT=self.raiz / "privados",
            MEDIA_ROOT=self.raiz / "publico",
        )
        self.settings.enable()
        self.addCleanup(self.settings.disable)

    @staticmethod
    def pdf(nombre="guia.pdf", contenido=b"%PDF-1.4\n1 0 obj\n"):
        return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")

    def test_pdf_privado_no_sobrescribe_y_no_existe_en_media_publica(self):
        uno = Path(guardar_PDFs(self.pdf(), user_id=7))
        dos = Path(guardar_PDFs(self.pdf(), user_id=7))
        self.assertNotEqual(uno.name, dos.name)
        self.assertTrue(uno.is_file() and dos.is_file())
        self.assertEqual(uno.parent, self.raiz / "privados" / "7" / "pdfs")
        self.assertFalse((self.raiz / "publico" / "pdfs").exists())
        self.assertEqual(self.client.get("/media/" + uno.name).status_code, 404)

    def test_rechaza_extension_falsa_o_cabecera_incorrecta(self):
        with self.assertRaises(ValidationError):
            guardar_PDFs(self.pdf("archivo.txt"), user_id=7)
        with self.assertRaises(ValidationError):
            guardar_PDFs(self.pdf(contenido=b"Esto no es PDF"), user_id=7)
        with self.assertRaises(ValidationError):
            guardar_PDFs(self.pdf(), user_id=None)
        self.assertFalse((self.raiz / "privados").exists())

    def test_rechaza_archivo_demasiado_grande_antes_de_guardar(self):
        with self.assertRaises(ValidationError):
            guardar_PDFs(self.pdf(contenido=b"%PDF-" + b"x" * (10 * 1024 * 1024)), user_id=7)
        self.assertFalse((self.raiz / "privados").exists())

    def test_audio_validado_por_cabecera_y_guardado_con_uuid(self):
        wav = b"RIFF" + (40).to_bytes(4, "little") + b"WAVE" + b"fmt " + b"\x00" * 32
        path = Path(guardar_audio(SimpleUploadedFile("nota.wav", wav), user_id=9))
        self.assertEqual(path.parent, self.raiz / "privados" / "9" / "audios")
        self.assertTrue(path.is_file())
        with self.assertRaises(ValidationError):
            validar_audio(SimpleUploadedFile("nota.wav", b"audio falso"))
        with self.assertRaises(ValidationError):
            validar_audio(SimpleUploadedFile("nota.exe", wav))

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_chat_rechaza_pdf_falso_antes_de_llamar_ia(self, obtener):
        user = User.objects.create_user("alumno_archivo", password="Segura!2026")
        self.client.force_login(user)
        bot = obtener.return_value
        bot.get_conversation_history.return_value = []
        bot.memory_manager.get_user_chats.return_value = []
        bot.memory_manager.get_cognitive_profile.return_value = {}
        respuesta = self.client.post(reverse("home"), {
            "prompt": "Resume este PDF", "archivo": self.pdf(contenido=b"Falso PDF"),
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("cabecera PDF", respuesta.context["chat_error"])
        bot.chat.assert_not_called()
        self.assertFalse((self.raiz / "privados").exists())


class PermisosDocentesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "admin_permisos", "admin_permisos@example.test", "Clave123!XYZ"
        )
        self.docente = User.objects.create_user("docente_permisos", password="Clave123!XYZ")
        perfil = PerfilUsuario.objects.create(user=self.docente)
        perfil.roles.add(Rol.objects.create(nombre="DOCENTE"))
        self.perfil_docente = perfil
        self.alumno = User.objects.create_user("estudiante_permisos", password="Clave123!XYZ")
        perfil_alumno = PerfilUsuario.objects.create(user=self.alumno)
        perfil_alumno.roles.add(Rol.objects.create(nombre="ESTUDIANTE"))
        sexo = Sexo.objects.create(descripcion="Prueba privacidad")
        persona = Persona.objects.create(
            perfil_user=perfil_alumno, nombre="Ana", apellido="Público",
            documento="PRIV-UNO", fecha_nacimiento=date(2009, 1, 1),
            direccion="Calle A", telefono="3001110000", sexo=sexo,
        )
        estudiante = Estudiante.objects.create(persona=persona)
        grado = Grado.objects.create(nombre="Once")
        self.curso_a = Curso.objects.create(nombre="11A", grado=grado)
        self.curso_b = Curso.objects.create(nombre="11B", grado=grado)
        self.anio_1 = AnioLectivo.objects.create(
            anio=2026, fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 1), activo=True
        )
        self.anio_2 = AnioLectivo.objects.create(
            anio=2027, fecha_inicio=date(2027, 1, 1), fecha_fin=date(2027, 12, 1), activo=True
        )
        self.matricula = Matricula.objects.create(
            estudiante=estudiante, curso=self.curso_a, anio_lectivo=self.anio_1
        )
        materia = Materia.objects.create(nombre="Matemáticas")
        tema = Tema.objects.create(materia=materia, nombre="Álgebra")
        nivel = NivelAprendizaje.objects.create(nombre="Básico")
        self.actividad = Actividad.objects.create(
            tema=tema, nivel=nivel, titulo="Álgebra básica", descripcion="Resolver ejercicios"
        )

    def test_docente_sin_asignacion_no_puede_crear_ni_asignar(self):
        self.client.force_login(self.docente)
        respuesta = self.client.get(reverse("panel_docente"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["matriculas"]), 0)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "matricula": self.matricula.pk, "actividad": self.actividad.pk
        }).status_code, 403)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "accion": "crear", "titulo": "Irregular",
        }).status_code, 403)
        self.assertEqual(ActividadAsignada.objects.count(), 0)

    def test_admin_puede_conceder_y_revocar_con_efecto_inmediato(self):
        self.client.force_login(self.admin)
        url = reverse("admin_asignaciones_docentes")
        respuesta = self.client.post(url, {
            "accion": "asignar", "docente": self.docente.pk,
            "curso": self.curso_a.pk, "anio_lectivo": self.anio_1.pk,
        })
        self.assertRedirects(respuesta, url)
        asignacion = AsignacionDocenteCurso.objects.get(docente=self.perfil_docente)
        self.client.force_login(self.docente)
        self.assertEqual(len(self.client.get(reverse("panel_docente")).context["matriculas"]), 1)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "matricula": self.matricula.pk, "actividad": self.actividad.pk
        }).status_code, 200)
        self.assertEqual(ActividadAsignada.objects.count(), 1)
        self.client.force_login(self.admin)
        self.assertRedirects(
            self.client.post(url, {"accion": "revocar", "asignacion_id": asignacion.pk}), url
        )
        asignacion.refresh_from_db()
        self.assertFalse(asignacion.activo)
        self.client.force_login(self.docente)
        self.assertEqual(len(self.client.get(reverse("panel_docente")).context["matriculas"]), 0)
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "matricula": self.matricula.pk, "actividad": self.actividad.pk
        }).status_code, 403)

    def test_autorizacion_compara_curso_y_anio_juntos(self):
        # Crea dos permisos cruzados: 11A/2026 y 11B/2027; 11A/2027 sigue prohibido.
        AsignacionDocenteCurso.objects.create(
            docente=self.perfil_docente, curso=self.curso_a, anio_lectivo=self.anio_1
        )
        AsignacionDocenteCurso.objects.create(
            docente=self.perfil_docente, curso=self.curso_b, anio_lectivo=self.anio_2
        )
        matricula_ajena = Matricula.objects.create(
            estudiante=self.matricula.estudiante, curso=self.curso_a, anio_lectivo=self.anio_2
        )
        self.client.force_login(self.docente)
        ids = {x.pk for x in self.client.get(reverse("panel_docente")).context["matriculas"]}
        self.assertEqual(ids, {self.matricula.pk})
        self.assertEqual(self.client.post(reverse("panel_docente"), {
            "matricula": matricula_ajena.pk, "actividad": self.actividad.pk
        }).status_code, 403)

    def test_estudiante_no_ve_administracion_docente(self):
        self.client.force_login(self.alumno)
        self.assertNotEqual(self.client.get(reverse("admin_asignaciones_docentes")).status_code, 200)
        self.assertNotEqual(self.client.post(reverse("admin_asignaciones_docentes"), {
            "accion": "asignar", "docente": self.docente.pk,
            "curso": self.curso_a.pk, "anio_lectivo": self.anio_1.pk,
        }).status_code, 200)
        self.assertFalse(AsignacionDocenteCurso.objects.exists())


class PrivacidadDatosTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin_privado", "admin@example.test", "Segura!2026")
        self.usuario = User.objects.create_user("alumno_privado", email="alumno@example.test", password="Segura!2026")
        perfil = PerfilUsuario.objects.create(user=self.usuario)
        sexo = Sexo.objects.create(descripcion="Femenino")
        persona = Persona.objects.create(
            perfil_user=perfil, nombre="Ana", apellido="Prueba",
            documento="PRIV-002", fecha_nacimiento=date(2008, 1, 1),
            direccion="Dirección privada", telefono="3000000000", sexo=sexo,
        )
        self.estudiante = Estudiante.objects.create(persona=persona)
        self.ajeno = User.objects.create_user("usuario_ajeno", email="secreto@example.test", password="Segura!2026")
        p2 = PerfilUsuario.objects.create(user=self.ajeno)
        Persona.objects.create(
            perfil_user=p2, nombre="Otro", apellido="Usuario",
            documento="PRIV-003", fecha_nacimiento=date(2008, 1, 1),
            direccion="Secreto de otro", telefono="3123456789", sexo=sexo,
        )

    def test_exportacion_exige_autenticacion_y_no_guarda_cache(self):
        url = reverse("exportar_mis_datos")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("application/json", respuesta["Content-Type"])
        self.assertIn("no-store", respuesta["Cache-Control"])
        self.assertIn("attachment;", respuesta["Content-Disposition"])

    def test_exportacion_excluye_datos_y_passwords_de_otros(self):
        self.client.force_login(self.usuario)
        datos = json.loads(self.client.get(reverse("exportar_mis_datos")).content)
        self.assertEqual(datos["cuenta"]["usuario"], "alumno_privado")
        self.assertEqual(datos["persona"]["documento"], "PRIV-002")
        todo = json.dumps(datos, ensure_ascii=False)
        self.assertNotIn("secreto@example.test", todo)
        self.assertNotIn("PRIV-003", todo)
        self.assertNotIn("password", todo.lower())

    def test_solo_administrador_puede_eliminar_cuentas(self):
        url = reverse("eliminar_admin_gestion_users", args=["usuarios", self.ajeno.pk])
        self.client.force_login(self.usuario)
        self.client.post(url)
        self.assertTrue(User.objects.filter(pk=self.ajeno.pk).exists())

    def test_eliminar_persona_elimina_cuenta_y_programa_purga_privada(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archivo = base / "privados" / str(self.usuario.pk) / "pdfs" / "adjunto.pdf"
            archivo.parent.mkdir(parents=True)
            archivo.write_bytes(b"%PDF-1.4")
            memoria = base / "ProyectoDeGrado" / "DATABASES" / "USERS" / str(self.usuario.pk)
            memoria.mkdir(parents=True)
            (memoria / "chats_meta.json").write_text("[]", encoding="utf-8")
            self.client.force_login(self.admin)
            persona_pk = Persona.objects.get(perfil_user__user=self.usuario).pk
            url = reverse("eliminar_admin_gestion_users", args=["personas", persona_pk])
            with override_settings(BASE_DIR=base, PRIVATE_UPLOAD_ROOT=base / "privados"):
                with self.captureOnCommitCallbacks(execute=True):
                    respuesta = self.client.post(url)
            self.assertEqual(respuesta.status_code, 302)
            self.assertFalse(User.objects.filter(pk=self.usuario.pk).exists())
            self.assertFalse(archivo.exists())
            self.assertFalse(memoria.exists())

    def test_no_se_puede_borrar_la_propia_cuenta_admin(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse(
            "eliminar_admin_gestion_users", args=["usuarios", self.admin.pk]
        ))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
