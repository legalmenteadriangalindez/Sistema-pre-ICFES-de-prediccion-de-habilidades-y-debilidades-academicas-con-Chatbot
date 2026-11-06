"""Regresiones de CSS: sintaxis, cascada, tokens y responsive.

Ejecutar: python -m unittest discover -s tests/styles -p 'test_*.py'
Requiere tinycss2, instalado en el trabajo CI específico de estilos.
"""
import re
import unittest
from pathlib import Path

import tinycss2


ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "Principal" / "static" / "css"
TEMPLATES = ROOT / "Principal" / "templates"


def reglas_css(source):
    """Comprueba errores de tokenización en hojas, declaraciones y media queries."""
    errores = []

    def recorrer(reglas, archivo):
        for regla in reglas:
            if regla.type == "error":
                errores.append(f"{archivo}: línea {regla.source_line}: {regla.message}")
                continue
            if regla.type == "qualified-rule":
                declaraciones = tinycss2.parse_declaration_list(
                    regla.content, skip_whitespace=True, skip_comments=True,
                )
                for declaracion in declaraciones:
                    if declaracion.type == "error":
                        errores.append(
                            f"{archivo}: línea {declaracion.source_line}: {declaracion.message}"
                        )
            elif regla.type == "at-rule" and regla.content is not None:
                if regla.lower_at_keyword in {
                    "media", "supports", "container", "layer", "keyframes",
                    "-webkit-keyframes",
                }:
                    recorrer(tinycss2.parse_rule_list(
                        regla.content, skip_whitespace=True, skip_comments=True
                    ), archivo)
                else:
                    for declaracion in tinycss2.parse_declaration_list(
                        regla.content, skip_whitespace=True, skip_comments=True,
                    ):
                        if declaracion.type == "error":
                            errores.append(
                                f"{archivo}: línea {declaracion.source_line}: {declaracion.message}"
                            )

    recorrer(tinycss2.parse_stylesheet(
        source, skip_whitespace=True, skip_comments=True
    ), "CSS")
    return errores


class CssQualityTests(unittest.TestCase):
    def test_hojas_css_sin_errores_de_sintaxis(self):
        archivos = sorted(STYLES.rglob("*.css"))
        self.assertGreaterEqual(len(archivos), 10)
        for archivo in archivos:
            with self.subTest(archivo=archivo.name):
                css = archivo.read_text(encoding="utf-8-sig")
                self.assertEqual(reglas_css(css), [])

    def test_orden_de_cascada_y_estilos_especificos_al_final(self):
        html = (TEMPLATES / "app_shell.html").read_text(encoding="utf-8")
        orden = [
            "css/styles.css", "css/design-tokens.css",
            "css/ui-2026.css", "css/ui-2026-chat.css",
            "css/ui-2026-pages.css", "css/ui-2026-academico.css",
            "css/ui-polish.css", "css/ui-polish-evaluaciones.css",
            "css/ui-polish-administracion.css",
            "css/ui-polish-preferencias.css",
            "css/portal-academico.css", "{% block extra_head %}",
        ]
        posiciones = [html.index(item) for item in orden]
        self.assertEqual(posiciones, sorted(posiciones))
        for pagina, nombre in [
            ("simulacros.html", "css/simulacros.css"),
            ("PlanSemanal.html", "css/plan-semanal.css"),
        ]:
            with self.subTest(pagina=pagina):
                self.assertIn(nombre, (TEMPLATES / pagina).read_text(encoding="utf-8"))

    def test_variables_de_diseno_definidas_y_referenciadas(self):
        css = (STYLES / "design-tokens.css").read_text(encoding="utf-8")
        definidas = set(re.findall(r"(--ds-[a-z0-9-]+)\s*:", css))
        requeridas = {
            "--ds-brand", "--ds-brand-strong", "--ds-navy", "--ds-surface",
            "--ds-canvas", "--ds-border", "--ds-focus", "--ds-font-body",
            "--ds-font-heading", "--ds-space-2", "--ds-button-min-height",
            "--ds-button-radius", "--ds-card-radius", "--ds-shadow-card",
        }
        self.assertTrue(requeridas.issubset(definidas))
        for pagina in (
            "ui-2026.css", "ui-2026-chat.css", "ui-2026-pages.css",
            "ui-2026-academico.css", "ui-polish.css",
            "ui-polish-evaluaciones.css",
            "ui-polish-administracion.css", "ui-polish-preferencias.css",
            "portal-academico.css", "plan-semanal.css",
        ):
            contenido = (STYLES / pagina).read_text(encoding="utf-8")
            faltantes = set(re.findall(r"var\((--ds-[a-z0-9-]+)", contenido)) - definidas
            self.assertEqual(faltantes, set(), pagina)
        self.assertIn("--pc-navy: var(--ds-navy)", css)
        self.assertIn("--px-blue: var(--ds-brand-polish)", css)

    def test_no_regresan_important_duplicados(self):
        layer = "".join(
            (STYLES / f).read_text(encoding="utf-8")
            for f in (
                "ui-2026.css", "ui-2026-chat.css",
                "ui-2026-pages.css", "ui-2026-academico.css",
            )
        )
        polish = "".join(
            (STYLES / f).read_text(encoding="utf-8")
            for f in (
                "ui-polish.css", "ui-polish-evaluaciones.css",
                "ui-polish-administracion.css", "ui-polish-preferencias.css",
            )
        )
        # Antes: 73 + 43. Después de quitar duplicaciones exactas: <= 112.
        self.assertLessEqual(layer.count("!important") + polish.count("!important"), 112)
        self.assertIn(".preicfes-ui.theme-dark", polish)
        self.assertIn(".preicfes-ui.reduce-motion", polish)
        self.assertIn(".preicfes-ui .pregunta-simulacro[hidden]", polish)

    def test_hojas_antes_minificadas_son_legibles(self):
        limites = {
            "ui-2026.css": 200,
            "ui-2026-chat.css": 200,
            "ui-2026-pages.css": 200,
            "ui-2026-academico.css": 200,
            "ui-polish.css": 255,
            "ui-polish-evaluaciones.css": 255,
            "ui-polish-administracion.css": 255,
            "ui-polish-preferencias.css": 255,
            "portal-academico.css": 120,
            "plan-semanal.css": 120,
        }
        for archivo, limite in limites.items():
            with self.subTest(css=archivo):
                lineas = (STYLES / archivo).read_text(encoding="utf-8").splitlines()
                self.assertGreater(len(lineas), 150)
                self.assertLessEqual(max(map(len, lineas)), limite)

    def test_permanecen_reglas_responsive(self):
        basico = "".join(
            f.read_text(encoding="utf-8")
            for f in sorted(STYLES.glob("ui-2026*.css"))
        )
        pulido = "".join(
            f.read_text(encoding="utf-8")
            for f in sorted(STYLES.glob("ui-polish*.css"))
        )
        semanal = (STYLES / "plan-semanal.css").read_text(encoding="utf-8")
        portal = (STYLES / "portal-academico.css").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:700px)", basico)
        self.assertIn("@media(max-width:420px)", pulido)
        self.assertIn("@media(max-width:680px)", semanal)
        self.assertIn("@media(max-width:850px)", portal)


if __name__ == "__main__":
    unittest.main()
