# Fase 2: consolidación CSS y diseño visual de Pre-ICFES

## Alcance y compatibilidad

Esta fase solo modifica presentación y pruebas de estilos.
**No cambia HTML funcional, JavaScript, rutas, vistas, modelos, migraciones,
datos de SQLite, permisos, evaluaciones ni integración con Ollama.**

La meta es dejar una cascada explícita, design tokens centralizados y archivos
legibles. Para evitar regresiones, se conservan los selectores, el orden
relativo de reglas originales, los breakpoints y las excepciones
`!important` que siguen siendo necesarias en el modo oscuro y al convivir
con las vistas heredadas.

## Orden de hojas en `app_shell.html`

1. Bootstrap y Font Awesome (librerías).
2. `styles.css`: estilos heredados. También lo usan páginas públicas que
   **no** heredan `app_shell.html`, por eso no debe eliminarse aún.
3. `design-tokens.css`: variables de colores, familias tipográficas,
   espacios, botones, radios y sombras, más alias de componentes anteriores.
4. `ui-2026.css` y `ui-2026-chat.css`,
   `ui-2026-pages.css`, `ui-2026-academico.css`: primera capa del
   rediseño, **en el mismo orden en que estaban las reglas antes**.
5. `ui-polish.css` y `ui-polish-evaluaciones.css`,
   `ui-polish-administracion.css`, `ui-polish-preferencias.css`:
   ajustes de componentes y modo oscuro en el orden original.
6. `portal-academico.css`: elementos del seguimiento y la orientación.
7. `{% block extra_head %}`: **estilos de página al final**, por ejemplo
   `simulacros.css` o `plan-semanal.css`.

No cambiar el orden de los archivos 4 o 5 por orden alfabético: son una
secuencia de cascada intencional. Cada uno se separó únicamente en los
límites de reglas top-level, nunca dentro de `@media` o selectores.

## Variables de diseño

`design-tokens.css` ofrece `--ds-brand`, `--ds-brand-strong`,
`--ds-canvas`, `--ds-surface`, `--ds-border`, `--ds-focus`,
`--ds-font-body`, `--ds-font-heading`, `--ds-space-1` a
`--ds-space-8`, `--ds-button-min-height`, `--ds-button-radius`,
`--ds-card-radius` y sombras.

Los alias `--pc-*` y `--px-*` conservan los valores de las hojas
existentes para migrar poco a poco los componentes, sin sustituir
arbitrariamente tonos que antes tenían matices diferentes.

**Modo oscuro:** el archivo `ui-polish-preferencias.css` continúa con
sus selectores `.theme-dark`, incluyendo excepciones de importancia.
No reemplazar colores oscuros por variables claras de superficie.
Las preferencias siguen en `preicfes.ui.v2` y no se modificó JavaScript.

## Reducción de duplicación y formato

- Se quitaron cuatro declaraciones idénticas que repetían `!important`
  para elementos del chat y que ya estaban definidas con el mismo selector
  y valor en la capa anterior. El total de `!important` en las capas
  principales pasó de **116 a 112**.
- Se dejaron intactos los `!important` que permiten superponer estilos
  heredados, ocultar preguntas del simulacro y atender el modo oscuro:
  eliminarlos indiscriminadamente modificaría la apariencia o accesibilidad.
- `ui-2026.css`, `ui-polish.css`, `portal-academico.css` y
  `plan-semanal.css` fueron formateados para que cada declaración sea
  legible, con reglas, comentarios y media queries en bloques separados.
- Las capas muy largas se dividieron por grupos funcionales en
  archivos manejables; no se cambiaron los valores CSS con excepción de
  referencias a tokens que conservan exactamente los mismos valores.
- `styles.css` conserva por seguridad las reglas de compatibilidad para
  Login y Registro; su retirada integral requiere la fase posterior de
  normalización de plantillas públicas.

## Validación automática

GitHub Actions ahora tiene tres trabajos independientes:

- `frontend`: sintaxis JavaScript y pruebas Node de componentes.
- `styles`: parser CSS TinyCSS2 en todas las hojas, tokens sin referencias
  faltantes, orden de cascada, legibilidad, media queries e importancia
  de declaraciones.
- `django`: `manage.py check`, integridad de migraciones y todos los
  tests actuales del backend.

Prueba local de CSS, con Python:

```powershell
python -m pip install "tinycss2>=1.3,<2"
python -m unittest discover -s tests/styles -p "test_*.py" -v
```

Los tests verifican integridad estructural, no sustituyen el análisis
visual real. Antes de producción revisar en navegador las vistas Inicio,
Chat, Configuración (claro/oscuro), Simulacros, Plan semanal, Administración,
Login, Registro y vistas móviles (360, 768 y 1280 px), incluida navegación
por teclado.

No es necesario volver a crear ni migrar la base de datos.
