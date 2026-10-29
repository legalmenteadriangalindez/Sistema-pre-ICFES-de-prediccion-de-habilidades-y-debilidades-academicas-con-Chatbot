"""Pruebas de regresión de registro, permisos, CRUD y cuestionarios.

Los servicios de IA se sustituyen con mocks: estas pruebas no requieren Ollama.
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Estudiante, Grado, PerfilUsuario, Persona, Rol, Sexo, IntentoEvaluacion, RespuestaEvaluacion


class RegistroTests(TestCase):
    def setUp(self):
        self.sexo = Sexo.objects.create(descripcion="Prueba")

    @patch("Principal.views.enviar_verificacion")
    def test_registro_crea_relaciones_y_rol(self, enviar):
        response = self.client.post(reverse("registro"), {
            "username": "alumno_prueba",
            "email": "alumno@example.com",
            "password1": "ClavePrueba2026!f",
            "password2": "ClavePrueba2026!f",
            "nombre": "Alumno",
            "apellido": "Ejemplo",
            "documento": "1000012345",
            "fecha_nacimiento": "2008-01-15",
            "direccion": "Calle de prueba 1",
            "telefono": "3001234567",
            "sexo": self.sexo.pk,
            "necesidades_especiales": "",
        })
        self.assertEqual(response.status_code, 200)
        enviar.assert_called_once()
        user = User.objects.get(username="alumno_prueba")
        self.assertFalse(user.is_active)
        perfil = PerfilUsuario.objects.get(user=user)
        self.assertTrue(perfil.roles.filter(nombre="ESTUDIANTE").exists())
        persona = Persona.objects.get(perfil_user=perfil)
        self.assertTrue(Estudiante.objects.filter(persona=persona).exists())

    @patch("Principal.views.enviar_verificacion")
    def test_verificacion_activa_cuenta(self, enviar):
        from Principal.services.verificacion_correo import crear_token
        usuario = User.objects.create_user("pendiente", "pendiente@example.com", "ClavePrueba2026!f", is_active=False)
        url = reverse("verificar_correo", args=[crear_token(usuario)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)

    def test_token_invalido_no_activa_cuenta(self):
        usuario = User.objects.create_user("sin_verificar", "sin_verificar@example.com", "ClavePrueba2026!f", is_active=False)
        response = self.client.get(reverse("verificar_correo", args=["token-falso"]))
        self.assertEqual(response.status_code, 400)
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)

    def test_registro_invalido_no_crea_usuario(self):
        response = self.client.post(reverse("registro"), {
            "username": "sin_datos", "password1": "abc", "password2": "xyz"
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sin_datos").exists())


class PermisosYCrudTests(TestCase):
    def setUp(self):
        self.estudiante = User.objects.create_user("estudiante", password="clave-test")
        perfil = PerfilUsuario.objects.create(user=self.estudiante)
        perfil.roles.add(Rol.objects.create(nombre="ESTUDIANTE"))
        self.admin = User.objects.create_superuser("administrador", "admin@example.com", "clave-test")
        self.grado = Grado.objects.create(nombre="Décimo")

    def test_estudiante_no_accede_a_gestiones(self):
        self.client.force_login(self.estudiante)
        for nombre in ("admin_gestion_db", "admin_gestion_users",
                       "admin_gestion_academica", "gestion_acudientes_estudiantes"):
            with self.subTest(vista=nombre):
                response = self.client.get(reverse(nombre))
                self.assertNotEqual(response.status_code, 200)

    def test_admin_puede_consultar_gestion_db(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_gestion_db"))
        self.assertEqual(response.status_code, 200)

    def test_eliminacion_por_get_no_modifica_datos(self):
        self.client.force_login(self.admin)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_estudiante_no_puede_eliminar(self):
        self.client.force_login(self.estudiante)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.client.post(url)
        self.assertTrue(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_admin_elimina_por_post(self):
        self.client.force_login(self.admin)
        url = reverse("eliminar_admin_gestion_academico", args=["grados", self.grado.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Grado.objects.filter(pk=self.grado.pk).exists())

    def test_admin_crea_rol(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin_gestion_db"), {
            "form": "roles", "nombre": "DOCENTE", "descripcion": "Rol de prueba"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Rol.objects.filter(nombre="DOCENTE").exists())


class CuestionarioTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("quiz_user", password="clave-test")
        self.client.force_login(self.usuario)

    @patch("Principal.views.generar_material", return_value=["Álgebra"])
    @patch("Principal.views.generar_quizes", return_value=[{
        "pregunta": "¿Cuánto es 2 + 2?", "A": "3", "B": "4",
        "C": "5", "D": "6", "respuesta_correcta": "B",
    }])
    def test_cuestionario_llama_generador_y_recomendador(self, generar, materiales):
        response = self.client.post(reverse("test"), {"materia": "Matemáticas"})
        self.assertEqual(response.status_code, 200)
        generar.assert_called_once_with("Matemáticas", 1)
        materiales.assert_called_once()
        self.assertEqual(response.context["materiales_recomendados"], ["Álgebra"])


class PruebasInglesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("ingles_prueba", password="clave-test")
        self.client.force_login(self.usuario)
        from .models import IntentoEvaluacion, RespuestaEvaluacion
        self.IntentoEvaluacion = IntentoEvaluacion
        self.RespuestaEvaluacion = RespuestaEvaluacion
        perfil = PerfilUsuario.objects.create(user=self.usuario)
        sexo = Sexo.objects.create(descripcion="Prueba inglés")
        persona = Persona.objects.create(perfil_user=perfil, nombre="Alumno", apellido="Prueba", documento="99887766", fecha_nacimiento="2008-01-01", direccion="Calle 1", telefono="3001234567", sexo=sexo)
        Estudiante.objects.create(persona=persona)

    def test_generacion_no_expone_claves(self):
        response = self.client.post(reverse("test"), {"materia": "Ingles"})
        self.assertEqual(response.status_code, 200)
        preguntas = response.context["preguntas_ingles"]
        self.assertEqual(len(preguntas), 10)
        self.assertEqual({p["tipo"] for p in preguntas}, {"aviso", "texto"})
        self.assertTrue(all("respuesta_correcta" not in p for p in preguntas))
        self.assertEqual(len(self.client.session["prueba_ingles_preguntas"]), 10)

    def test_calificacion_persiste_respuestas_y_competencias(self):
        self.client.post(reverse("test"), {"materia": "Ingles"})
        preguntas = self.client.session["prueba_ingles_preguntas"]
        respuestas = {f"respuesta_{p['id']}": p["respuesta_correcta"] for p in preguntas}
        response = self.client.post(reverse("test"), {"verificar_ingles": "1", **respuestas})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resultado_ingles"]["porcentaje"], 100)
        self.assertEqual(self.IntentoEvaluacion.objects.count(), 1)
        self.assertEqual(self.RespuestaEvaluacion.objects.count(), 10)
        self.assertEqual(len(response.context["competencias_ingles"]), 2)
        self.assertNotIn("prueba_ingles_preguntas", self.client.session)

    def test_no_permite_recalificar(self):
        self.client.post(reverse("test"), {"materia": "Ingles"})
        preguntas = self.client.session["prueba_ingles_preguntas"]
        respuestas = {f"respuesta_{p['id']}": p["respuesta_correcta"] for p in preguntas}
        self.client.post(reverse("test"), {"verificar_ingles": "1", **respuestas})
        response = self.client.post(reverse("test"), {"verificar_ingles": "1", **respuestas})
        self.assertIn("error_prueba", response.context)
        self.assertEqual(self.IntentoEvaluacion.objects.count(), 1)


class SimulacrosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("simulacro_user", password="clave-test")
        self.client.force_login(self.usuario)
        perfil = PerfilUsuario.objects.create(user=self.usuario)
        sexo = Sexo.objects.create(descripcion="Prueba simulacro")
        persona = Persona.objects.create(perfil_user=perfil, nombre="Alumno", apellido="Simulacro", documento="99887767", fecha_nacimiento="2008-01-01", direccion="Calle 2", telefono="3001234568", sexo=sexo)
        Estudiante.objects.create(persona=persona)

    def test_iniciar_materia_no_expone_claves(self):
        response = self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Matemáticas"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["preguntas"]), 2)
        self.assertTrue(all("correcta" not in p for p in response.context["preguntas"]))

    def test_integral_cubre_cinco_materias(self):
        response = self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Integral"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len({p["materia"] for p in response.context["preguntas"]}), 5)

    def test_finalizar_guarda_calificacion(self):
        self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Matemáticas"})
        preguntas = self.client.session["simulacro_activo"]["preguntas"]
        respuestas = {"respuesta_" + str(p["id"]): p["correcta"] for p in preguntas}
        response = self.client.post(reverse("simulacros"), {"accion": "finalizar", **respuestas})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resultado"]["aciertos"], 2)
        self.assertEqual(IntentoEvaluacion.objects.filter(materia="Simulacro: Matemáticas").count(), 1)
        self.assertEqual(RespuestaEvaluacion.objects.count(), 2)

    def test_no_recalifica_dos_veces(self):
        self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Matemáticas"})
        self.client.post(reverse("simulacros"), {"accion": "finalizar"})
        response = self.client.post(reverse("simulacros"), {"accion": "finalizar"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(IntentoEvaluacion.objects.count(), 1)

    def test_rechaza_envio_fuera_de_plazo(self):
        self.client.post(reverse("simulacros"), {"accion": "iniciar", "materia": "Matemáticas"})
        sesion = self.client.session
        activo = sesion["simulacro_activo"]
        activo["vence"] = 1
        sesion["simulacro_activo"] = activo
        sesion.save()
        response = self.client.post(reverse("simulacros"), {"accion": "finalizar"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(IntentoEvaluacion.objects.count(), 0)


class TutorAcademicoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("tutor_estudiante", password="clave-test")
        self.client.force_login(self.usuario)
        perfil = PerfilUsuario.objects.create(user=self.usuario)
        sexo = Sexo.objects.create(descripcion="Sexo tutor")
        persona = Persona.objects.create(perfil_user=perfil, nombre="Estudiante", apellido="Tutor", documento="12345678901", fecha_nacimiento="2008-01-01", direccion="Calle 3", telefono="3001234569", sexo=sexo)
        self.estudiante = Estudiante.objects.create(persona=persona)

    @patch("Principal.views.chatbotManager.get_chatbot")
    def test_chat_recibe_resultados_reales(self, obtener):
        from unittest.mock import MagicMock
        bot = MagicMock()
        bot.get_conversation_history.return_value = []
        bot.memory_manager.get_user_chats.return_value = []
        bot.memory_manager.get_cognitive_profile.return_value = {}
        bot.chat.return_value = {"success": True, "response": "Practiquemos paso a paso."}
        obtener.return_value = bot
        IntentoEvaluacion.objects.create(estudiante=self.estudiante, materia="Inglés", total_preguntas=10, aciertos=6)
        response = self.client.post(reverse("home"), {"prompt": "Ayúdame con inglés"})
        self.assertEqual(response.status_code, 200)
        contexto = bot.chat.call_args.kwargs["academic_context"]
        self.assertIn("Inglés: 6 de 10", contexto)


class HistorialAcademicoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("historial_alumno", password="clave-test")
        self.client.force_login(self.usuario)
        perfil = PerfilUsuario.objects.create(user=self.usuario)
        sexo = Sexo.objects.create(descripcion="Historial")
        persona = Persona.objects.create(perfil_user=perfil, nombre="Alumno", apellido="Historial", documento="123450001", fecha_nacimiento="2008-01-01", direccion="Calle 4", telefono="3001112233", sexo=sexo)
        self.estudiante = Estudiante.objects.create(persona=persona)

    def test_historial_compara_evaluaciones(self):
        IntentoEvaluacion.objects.create(estudiante=self.estudiante, materia="Inglés", total_preguntas=10, aciertos=5)
        IntentoEvaluacion.objects.create(estudiante=self.estudiante, materia="Inglés", total_preguntas=10, aciertos=8)
        response = self.client.get(reverse("historial_academico"))
        self.assertEqual(response.status_code, 200)
        serie = response.context["series"][0]
        self.assertEqual(serie["ultima"]["cambio"], 30.0)
        self.assertEqual(serie["ultima"]["tendencia"], "Mejorando")

    def test_historial_no_muestra_evaluaciones_ajenas(self):
        otro = User.objects.create_user("otro_historial", password="clave-test")
        perfil = PerfilUsuario.objects.create(user=otro)
        sexo = Sexo.objects.first()
        persona = Persona.objects.create(perfil_user=perfil, nombre="Otro", apellido="Alumno", documento="123450002", fecha_nacimiento="2008-01-01", direccion="Calle 5", telefono="3001112244", sexo=sexo)
        estudiante_ajeno = Estudiante.objects.create(persona=persona)
        IntentoEvaluacion.objects.create(estudiante=estudiante_ajeno, materia="Ciencias Naturales", total_preguntas=10, aciertos=2)
        response = self.client.get(reverse("historial_academico"))
        self.assertEqual(response.context["total_intentos"], 0)
        self.assertNotContains(response, "Ciencias Naturales")
