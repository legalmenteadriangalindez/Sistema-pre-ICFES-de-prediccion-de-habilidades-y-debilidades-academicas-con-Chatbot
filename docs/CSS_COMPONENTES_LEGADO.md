# Refactorización CSS heredado por componentes

## Compatibilidad intencional

Se dividió `Principal/static/css/styles.css` en diez hojas
`Principal/static/css/legacy/*.css`, sin modificar ninguna regla, selector,
declaración, comentario, breakpoint, orden o JavaScript.

`styles.css` sigue siendo la entrada pública: utiliza diez `@import url()`
en el orden exacto del archivo anterior. No se cambiaron templates, rutas,
modelos ni el CSS 2026. Por eso también siguen funcionando las páginas
públicas que enlazan directamente a `styles.css`.

## Organización

1. `01-base-preferencias.css`
2. `02-chat-controles.css`
3. `03-chat-historial-modo-oscuro.css`
4. `04-footer-lista-chats.css`
5. `05-responsive-navegacion.css`
6. `06-modales-chat.css`
7. `07-refresh-estructura.css`
8. `08-refresh-componentes.css`
9. `09-refresh-chat-footer.css`
10. `10-refresh-oscuro-paginas.css`

El orden numérico representa el orden original de la cascada; **no ordenar
alfabéticamente ni mover reglas entre archivos** sin una revisión visual y
sus correspondientes pruebas. Las hojas antiguas contienen overrides con
especificidad y media queries deliberados.

## Comprobación de equivalencia y pruebas

El archivo original tenía el Git blob SHA-1
`80858521cbe3990690c5785d87127a06318808af`.
`tests/styles/test_legacy_css_components.py` vuelve a concatenar los
componentes en orden y compara el SHA de Git calculado con los bytes; así se
comprueba que los estilos originales permanecen **idénticos**.

El test Playwright `legacy-css.spec.cjs` verifica la carga HTTP de todos
los fragmentos en el navegador, junto con los demás flujos responsive y
visuales de la suite. No se hizo una sustitución de clases ni se ajustaron
colores, contrastes o espaciados.

Ejecutar:
```powershell
python -m unittest discover -s tests/styles -p "test_*.py" -v
npm run test:browser
```

Antes del despliegue, revisar si el servidor y el CDN respetan las rutas
relativas `/static/css/legacy/`. `collectstatic` conserva estos archivos.
En producción, publicar CSS y su caché de manera coherente.
