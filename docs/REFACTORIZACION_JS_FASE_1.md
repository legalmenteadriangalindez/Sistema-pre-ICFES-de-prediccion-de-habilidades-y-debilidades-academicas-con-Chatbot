# Fase 1 — JavaScript modular y sin dependencias de DOM entre páginas

Esta fase reorganiza JavaScript y mantiene las rutas, vistas, reglas de negocio,
migraciones y base de datos existentes. **No requiere migraciones nuevas.**

## Carga y responsabilidad única

| Archivo | Dónde se carga | Responsabilidad |
| --- | --- | --- |
| `Principal/static/js/ui-2026.js` | Plantilla `app_shell.html` | Abrir/cerrar la navegación lateral |
| `Principal/static/js/ui-polish.js` | `app_shell.html` | Preferencias de apariencia y accesibilidad |
| `Principal/static/js/confirmations.js` | `app_shell.html` | Confirmaciones de formularios `data-confirm` |
| `Principal/static/js/chat.js` | Únicamente `home.html` | Composer, adjuntos, sugerencias y envío del tutor |
| `Principal/static/js/audio-recorder.js` | Únicamente `home.html` | Pedir permiso, grabar, parar, adjuntar y liberar micrófono |
| `Principal/static/js/admin-users.js` | Únicamente `admin_gestion_user.html` | Buscar y filtrar filas de usuarios |
| `Principal/static/js/simulacros.js` | Únicamente `simulacros.html` | Mantiene lógica existente de preguntas y temporizador |
| `Principal/static/js/test.js` | Únicamente `TestDeVocacion.html` | Mantiene lógica existente de cuestionarios |

Se retiró `script.js`, que mezclaba preferencias, grabación, eliminación y
notificaciones, y cuatro archivos JS de cero bytes sin referencias en las
plantillas: `configuracion.js`, `inicioDeSesion.js`, `perfil.js` y
`registro.js`. No tenían implementación funcional que preservar.

## Compatibilidad y manejo de errores

- Se **mantiene** la clave `localStorage["preicfes.ui.v2"]`, las clases
  `theme-dark` y `reduce-motion` y la variable CSS `--pc-text-scale`.
  Si esa clave no existe, se toma una sola vez el valor histórico
  `modoOscuro` (cuando lo permita el navegador).
- Cada módulo comprueba que los botones y controles necesarios existan. Si
  se abre una vista sin micrófono o sin chat, los scripts globales no
  intentan acceder a esos elementos.
- Las confirmaciones de eliminación o revocación usan un único listener
  delegado en formularios `data-confirm`; no se escribe `onsubmit`
  en las plantillas.
- El micrófono se detiene y libera sus pistas al finalizar o fallar. Se
  maneja rechazo de permisos, grabadores no admitidos y archivos vacíos o
  mayores que 25 MB. En navegadores compatibles se usa WebM, OGG o M4A.
- La filtración de usuarios solo modifica la visibilidad de filas, sin
  enviar, editar ni borrar datos.

## Pruebas

Se añadieron diez pruebas sin dependencias de terceros mediante Node 22:
`tests/javascript/smoke.test.cjs`. Incluyen vistas sin controles,
navegación, preferencias, migración de modo oscuro, chat, filtro, confirmaciones
y grabación con micrófono simulado (sin pedir permiso real).

```powershell
node --test tests/javascript/smoke.test.cjs
python manage.py check
python manage.py test Principal
```

GitHub Actions ejecuta **dos trabajos**: JavaScript (sintaxis y smoke tests)
y Django (todas las pruebas). Solo debe fusionarse si los dos son exitosos.

**Alcance:** las pruebas Node simulan el DOM, no son una prueba visual real de
Chrome/Firefox/Safari ni verifican dispositivos físicos de micrófono. Para
validar en navegador, entrar como estudiante, enviar texto y audio al tutor,
abrir Configuraciones, cambiar preferencias, filtrar en Gestión de usuarios y
comprobar los botones de confirmación en sus páginas respectivas. En todas
las páginas, revisar la consola del navegador en busca de errores.

Esta fase **no cambia** estilos CSS, autenticación, calificaciones, LLM,
persistencia de chats ni modelos de Django.
