# Fase 7 — Controles automáticos de calidad (Pre-ICFES)

## Qué se incorporó

| Ámbito | Herramienta | Qué bloquea una actualización |
| --- | --- | --- |
| Python | Ruff | Errores críticos en el proyecto completo; reglas E/F/I estrictas en archivos adoptados |
| Python | Black | Formato invariable de `tests/browser/seed_ci.py` y `json_storage.py` |
| JavaScript | ESLint 10 | Variables indefinidas, código sin usar, `eval`, `debugger`; todos los JS de la aplicación y las pruebas de navegador |
| CSS | Stylelint 17 | Errores CSS en hojas del proyecto, con excepciones documentadas para duplicación heredada |
| CSS | TinyCSS2 | Sintaxis, tokens, orden de cascada, media queries y compatibilidad |
| Django | Test runner | Suite completa de modelos, formularios, seguridad, permisos, chat, predicción y HTML |
| Navegador real | Playwright Chromium | Login, permisos, filtros, confirmaciones, preferencias, alertas, responsive y errores JS |

GitHub Actions ejecuta cinco trabajos independientes: `python-quality`,
`frontend`, `styles`, `django` y `browser` en todos los Pull Requests
y en push a `main`. Una comprobación de calidad fallida impide **que nosotros
fusionemos el PR**. Para impedir también fusiones manuales se deben configurar
las reglas de protección de la rama `main` con estos cinco checks obligatorios.

## Adopción progresiva y deuda técnica explícita

La aplicación ya contiene código histórico que no está enteramente formateado
con Black. Por seguridad NO se reescribió todo el repositorio en esta fase.

- `ruff check .` detecta errores graves de sintaxis y nombres en todo el
  código fuente, excluyendo migraciones y artefactos.
- `ruff check --select E,F,I ...` aplica la comprobación estricta inicialmente
  a la nueva semilla de E2E y al servicio pequeño `json_storage.py`.
- `black --check ...` bloquea regresiones de formato en esos mismos archivos.
- `npm run lint:js` analiza el JavaScript de la app y los tests de navegador.
- `npm run lint:css` analiza los CSS del proyecto. La regla específica
  `no-duplicate-selectors` queda temporalmente deshabilitada por la capa
  legacy; el resto de la configuración recomendada continúa activo.

Los siguientes módulos de Python y CSS se pueden sumar al conjunto estricto
uno a uno, con un PR separado y pruebas previas. Las excepciones no deben
crecer silenciosamente. Los criterios mínimos siguen siendo obligatorios.

## Navegador: datos e independencia de IA

Las pruebas están en `tests/browser/*.spec.cjs`, con un servidor Django local
en el puerto 8765 y una **base SQLite desechable** `ci-browser.sqlite3`.
`seed_ci.py` se niega a ejecutarse si la variable `CI` no está activa o si
la base no tiene ese nombre. Se crean dos cuentas artificiales, solo para CI.

Las pruebas no requieren Ollama, Chroma real, internet del navegador ni
configuración de Brevo. Se prueba Chrome/Chromium en CI; Firefox y WebKit
se podrán añadir después de estabilizar la ejecución y el entorno.

Cuando Playwright falla, GitHub conserva durante siete días las capturas y
trazas para facilitar la depuración. No se deben introducir datos reales de
estudiantes, mensajes privados ni contraseñas de producción en estos tests.

## Cómo ejecutar localmente

Requisitos: Python 3.12, Node.js 22, dependencias Python del proyecto y
Chromium de Playwright instalados.

```powershell
pip install -r requirements-quality.txt
npm install
ruff check .
ruff check --select E,F,I tests/browser/seed_ci.py Principal/IA/LangGraph/graph_chatbot/json_storage.py
black --check tests/browser/seed_ci.py Principal/IA/LangGraph/graph_chatbot/json_storage.py
npm run lint:js
npm run lint:css
npm run test:js
python manage.py check
python manage.py test Principal
```

Para ejecutar Playwright localmente, **no utilices tu base de datos habitual**.
Prepara manualmente una base separada de pruebas y cuentas de prueba, con
`DJANGO_DB_PATH=ci-browser.sqlite3`. La semilla automática está restringida
a CI y no debe utilizarse para la base real.

```powershell
npx playwright install chromium
npm run test:browser
```

## Para hacer obligatorios los resultados en GitHub

En el repositorio, abrir **Settings → Branches / Rulesets** y configurar
protección de `main`: exigir Pull Request, prohibir merge sin checks, y
seleccionar `Ruff y Black`, `ESLint y pruebas JavaScript`,
`Stylelint y CSS`, `Django: pruebas y migraciones` y
`Playwright Chromium`. Se recomienda exigir que la rama esté actualizada
antes de fusionar y prohibir bypass a administradores. Este ajuste del
repositorio no se modifica desde un archivo de código.

## Alcance

La fase solo añade controles, scripts y datos de prueba. No modifica los
modelos, migraciones, URLs, permisos, evaluaciones ni resultados reales.
La validación de navegador con datos simulados no equivale a una auditoría
de seguridad completa ni a una prueba real de Ollama.
