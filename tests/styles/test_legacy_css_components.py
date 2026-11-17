"""Garantía de equivalencia del CSS histórico y de sus puntos de carga."""
import hashlib
import re
import unittest
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "Principal" / "static" / "css"
LEGACY = CSS / "legacy"
TEMPLATES = Path(__file__).resolve().parents[2] / "Principal" / "templates"
ORIGINAL_BLOB_SHA = "80858521cbe3990690c5785d87127a06318808af"
PARTS = (
    "01-base-preferencias.css",
    "02-chat-controles.css",
    "03-chat-historial-modo-oscuro.css",
    "04-footer-lista-chats.css",
    "05-responsive-navegacion.css",
    "06-modales-chat.css",
    "07-refresh-estructura.css",
    "08-refresh-componentes.css",
    "09-refresh-chat-footer.css",
    "10-refresh-oscuro-paginas.css",
)


class LegacyCssComponentsTests(unittest.TestCase):
    def test_manifiesto_importa_todos_los_componentes_en_orden(self):
        manifest = (CSS / "dashboard-legacy.css").read_text(encoding="utf-8")
        imports = re.findall(
            r'@import\s+url\(["\']\./legacy/([^"\']+)["\']\)\s*;',
            manifest,
        )
        self.assertEqual(imports, list(PARTS))
        self.assertEqual(len(imports), len(set(imports)))

    def test_fachada_historica_apunta_al_manifiesto_nuevo(self):
        compat = (CSS / "styles.css").read_text(encoding="utf-8")
        self.assertIn('@import url("./dashboard-legacy.css");', compat)

    def test_fragmentos_reconstruyen_exactamente_el_css_original(self):
        content = b"".join((LEGACY / part).read_bytes() for part in PARTS)
        header = b"blob " + str(len(content)).encode("ascii") + b"\0"
        self.assertEqual(hashlib.sha1(header + content).hexdigest(), ORIGINAL_BLOB_SHA)

    def test_dashboard_y_auth_tienen_cascadas_independientes(self):
        dashboard = (TEMPLATES / "app_shell.html").read_text(encoding="utf-8")
        orden = [
            "css/dashboard-legacy.css",
            "css/design-tokens.css",
            "css/components.css",
            "css/ui-2026.css",
            "css/ui-polish.css",
        ]
        posiciones = [dashboard.index(item) for item in orden]
        self.assertEqual(posiciones, sorted(posiciones))

        auth = (TEMPLATES / "auth_shell.html").read_text(encoding="utf-8")
        for required in (
            "css/design-tokens.css",
            "css/components.css",
            "css/auth-base.css",
            "css/account-pages.css",
        ):
            self.assertIn(required, auth)
        for forbidden in (
            "css/dashboard-legacy.css",
            "css/ui-2026.css",
            "css/ui-polish.css",
            "cdn.jsdelivr.net/npm/bootstrap",
        ):
            self.assertNotIn(forbidden, auth)


if __name__ == "__main__":
    unittest.main()
