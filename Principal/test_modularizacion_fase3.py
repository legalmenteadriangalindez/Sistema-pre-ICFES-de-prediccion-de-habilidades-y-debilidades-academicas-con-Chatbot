"""Contratos de compatibilidad para la modularización interna."""

from django.test import SimpleTestCase
from django.urls import reverse

from Principal.consultas.academico import _matricula as academic_selector
from Principal.consultas.identidad import es_gestor as identity_selector
from Principal.formularios.cuentas import UserRegisterForm as DomainUserForm
from Principal.forms import UserRegisterForm
from Principal.modelos.identidad import Persona as DomainPersona
from Principal.models import Persona
from Principal.services.perfiles import obtener_relaciones_perfil
from Principal.view_modules.selectores import _matricula, es_gestor


class ModularizacionFase3Tests(SimpleTestCase):
    def test_facades_preservan_las_clases_publicas(self):
        self.assertIs(Persona, DomainPersona)
        self.assertIs(UserRegisterForm, DomainUserForm)
        self.assertIs(_matricula, academic_selector)
        self.assertIs(es_gestor, identity_selector)

    def test_rutas_publicas_siguen_resolviendo(self):
        for name in (
            "home",
            "perfil",
            "perfil_editar",
            "password_change",
            "admin_gestion_users",
            "simulacros",
        ):
            with self.subTest(route=name):
                self.assertTrue(reverse(name).startswith("/"))

    def test_servicio_de_perfil_expone_la_operacion_de_dominio(self):
        self.assertTrue(callable(obtener_relaciones_perfil))
