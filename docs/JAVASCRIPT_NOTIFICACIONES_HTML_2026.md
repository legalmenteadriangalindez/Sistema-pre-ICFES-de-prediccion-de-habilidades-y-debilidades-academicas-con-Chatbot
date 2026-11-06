# Mantenimiento de JavaScript y legibilidad de plantillas — noviembre de 2026

## Resultado de la auditoría

La fase 1 ya había eliminado `script.js`, `perfil.js`, `configuracion.js`,
`registro.js` y `inicioDeSesion.js` al comprobar que eran código
heredado o archivos vacíos. **No se reintroducen**. Los ocho scripts
existentes tienen responsabilidades específicas.

| Módulo | Responsabilidad actual |
| --- | --- |
| `ui-polish.js` | Único controlador de preferencias: modo oscuro, texto, animaciones |
| `ui-2026.js` | Navegación y menú lateral |
| `chat.js` | Entrada del tutor y adjuntos |
| `audio-recorder.js` | Permisos y grabación del micrófono |
| `confirmations.js` | Confirmaciones delegadas con `data-confirm` |
| `admin-users.js` | Búsqueda y filtro de usuarios |
| `simulacros.js` | Interacciones del simulacro |
| `test.js` | Cuestionario de orientación |

## Mejora complementaria: notificaciones accesibles

Se añadieron `components/notifications.html`,
`static/js/notifications.js` y `static/css/notifications.css`.

- La plantilla `app_shell.html` contiene un único centro común de avisos
  de Django; los mensajes de `messages` se escapan automáticamente.
- Éxitos e información utilizan `role="status"`; errores y advertencias
  utilizan `role="alert"`.
- Cada aviso puede cerrarse con un botón etiquetado, sin `onclick`.
- `window.PreICFES.notify(texto, tono)` permite añadir mensajes desde
  otros módulos. Solo admite `success`, `warning` o `info` y usa
  `textContent`, nunca `innerHTML`.
- No se usa almacenamiento, temporizadores, ni llamadas de red, y el
  componente queda oculto cuando no hay mensajes.
- `PlanSemanal.html` ya no presenta dos veces los mismos mensajes.
- Los avisos incluyen reglas de modo oscuro y se cargan después de las
  capas globales de CSS y antes de los estilos específicos de página.

## Legibilidad de administración

`admin_gestion_user.html` se reformateó de 28 a aproximadamente 130
líneas, con indentación coherente. **No se cambiaron** URLs, permisos,
contexto de Django, variables de formulario, CSRF, IDs de filtros,
componentes reutilizados ni valores enviados por POST.

No se agregaron gestores de preferencias duplicados ni se reincorporó
el script global de micrófono.

## Pruebas

Se agregaron:
- Cuatro pruebas Node en `tests/javascript/notifications.test.cjs` que
  comprueban páginas sin contenedor, escape de HTML, tonos admitidos,
  cierre y coexistencia de varios avisos.
- Cinco pruebas Django en `Principal/test_notificaciones_ui.py` que
  comprueban renderizado de mensajes, roles accesibles, controlador único,
  carga CSS/JS, ausencia de duplicados y plantilla administrativa.

Comandos:
```powershell
node --test tests/javascript/*.test.cjs
python manage.py test Principal.test_notificaciones_ui -v 2
python manage.py test Principal
python -m unittest discover -s tests/styles -p 'test_*.py' -v
```

Los tests validan el DOM simulado y las plantillas; aún se recomienda
comprobar manualmente en navegador real el modo oscuro, mensajes y acciones
administrativas. La actualización no modifica modelos, tablas ni SQLite.
