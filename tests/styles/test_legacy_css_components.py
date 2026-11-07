"""Garantía de equivalencia byte a byte de la hoja CSS heredada.

El manifiesto debe cargar los fragmentos en la secuencia original exacta.
Un cambio accidental de estilo, media query o posición hace fallar la prueba.
"""
import hashlib
import re
import unittest
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "Principal" / "static" / "css"
LEGACY = CSS / "legacy"
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
        manifest = (CSS / "styles.css").read_text(encoding="utf-8")
        imports = re.findall(
            r'@import\s+url\(["\']\./legacy/([^"\']+)["\']\)\s*;',
            manifest,
        )
        self.assertEqual(imports, list(PARTS))
        self.assertEqual(len(imports), len(set(imports)))

    def test_fragmentos_reconstruyen_exactamente_el_css_original(self):
        content = b"".join((LEGACY / part).read_bytes() for part in PARTS)
        header = b"blob " + str(len(content)).encode("ascii") + b"\0"
        self.assertEqual(hashlib.sha1(header + content).hexdigest(), ORIGINAL_BLOB_SHA)

    def test_no_se_cambian_scripts_ni_orden_de_capas(self):
        html = (Path(__file__).resolve().parents[2] / "Principal" / "templates" / "app_shell.html").read_text(encoding="utf-8")
        self.assertLess(html.index("css/styles.css"), html.index("css/design-tokens.css"))
        self.assertLess(html.index("css/design-tokens.css"), html.index("css/ui-2026.css"))
        self.assertLess(html.index("css/ui-2026.css"), html.index("css/ui-polish.css"))


if __name__ == "__main__":
    unittest.main()
