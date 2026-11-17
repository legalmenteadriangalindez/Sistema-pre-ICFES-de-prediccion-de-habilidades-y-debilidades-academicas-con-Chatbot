# Inventario Fase 1 — Pre-ICFES

Estado: auditoría no funcional sobre la rama audit/fase1-inventario.

Este documento no elimina ni modifica vistas, modelos, rutas, plantillas ni estilos. La
auditoría deja un inventario reproducible y marca candidatos que deben verificarse antes
de retirar cualquier archivo.

## Alcance

1. Referencias estáticas de plantillas, CSS y JavaScript.
2. Definiciones y nombres de rutas Django.
3. Consultas ORM dentro de bucles y relaciones anidadas en plantillas.
4. Cobertura de pruebas sobre PostgreSQL.
5. Diferenciación preliminar entre flujo actual y legado.

El auditor reproducible está en scripts/audit_phase1.py. Genera un informe Markdown y
no importa Django ni escribe sobre el código de la aplicación.

## Tamaño actual del repositorio

El árbol de main contiene:

- 369 rutas en total.
- 341 archivos y 28 directorios.
- 166 archivos Python.
- 74 plantillas HTML.
- 36 hojas CSS.
- 12 módulos JavaScript y 11 archivos CJS.
- 18 migraciones Django.

Los archivos de mayor tamaño que requieren atención futura son:

- Principal/models.py: aproximadamente 769 líneas.
- Principal/services/prediccion_academica.py: aproximadamente 396 líneas.
- Principal/tests.py: aproximadamente 279 líneas.
- Principal/IA/LangGraph/graph_chatbot/chatbot.py: aproximadamente 332 líneas.
- Principal/forms.py: aproximadamente 383 líneas.

Esto no implica que deban dividirse durante esta fase; se registra para la siguiente
fase de modularización.

## Flujo actual identificado

### Autenticación y cuenta

El flujo actual utiliza:

- ProyectoDeGrado/urls.py para accounts/login/ y accounts/password_change/.
- Principal/account_forms.py para los formularios específicos de autenticación.
- Principal/templates/registration/login.html.
- Principal/templates/registration/password_change_form.html.
- Principal/templates/app_shell.html como base visual.
- Principal/static/css/account-pages.css.
- Principal/static/js/account-pages.js.

El cambio reciente de inicio de sesión, visibilidad de contraseña y cambio de contraseña
queda separado del formulario antiguo de registro.

### Perfil

El flujo de consulta actual pasa por:

- Principal/urls.py.
- Principal/views.py como fachada.
- Principal/view_modules/perfiles.py.
- Principal/templates/PerfilDeUsuarios.html.

Se conserva una vista antigua llamada editarPerfil y la plantilla
Principal/templates/PerfilDeUsuario.html. La vista no aparece conectada a una URL actual,
por lo que ambos elementos quedan marcados como candidatos heredados, no como archivos
eliminables todavía.

### Aplicación y dashboard

El flujo visual actual es:

- Principal/templates/app_shell.html.
- Principal/templates/home.html.
- design-tokens.css.
- ui-2026*.css.
- ui-polish*.css.
- portal-academico.css.
- notifications.css.
- accesibilidad-refuerzo.css.

La carga de CSS conserva una capa heredada inicial en styles.css. Esto debe mantenerse
hasta comprobar que no existen referencias dinámicas.

## Candidatos heredados a revisar

Estos elementos no se eliminan en la Fase 1:

- Principal/templates/InicioSesion.html.
- Principal/templates/PerfilDeUsuario.html.
- Principal/static/css/inicioDeSesiones.css.
- Principal/static/css/logins.css.
- Principal/static/css/perfile.css.
- Vista editarPerfil de Principal/view_modules/perfiles.py.
- Rutas con nombres antiguos como testDeVocacion, actividadesUsuario y
  gestion_acudientes_estudiantes.

La clasificación definitiva se obtiene con el artefacto phase1-inventory generado por
scripts/audit_phase1.py. Un archivo sin referencia estática puede ser usado por imports,
tests, nombres dinámicos o despliegues anteriores.

## Resultado automatizado de la auditoría

La ejecución del workflow de esta rama produjo el siguiente resumen:

- 74 plantillas HTML.
- 36 hojas CSS.
- 12 módulos JavaScript.
- 71 rutas detectadas y 68 nombres únicos.
- No se detectaron nombres de ruta duplicados.
- No se detectaron patrones de URL duplicados.
- Se detectó demo_publica como nombre sin referencia estática directa.
- Se detectaron 51 candidatos de consultas de lectura dentro de bucles o relaciones anidadas.

### Plantillas candidatas

- Carreras.html.
- PerfilDeUsuarioAdminAcademico.html.
- TutorDemoLimitado.html.
- components/tables/people_header.html.
- components/tables/person_row.html.
- components/tables/user_row.html.
- components/tables/users_header.html.
- cordinador.html.
- docentes.html.
- editarPerfilDeUsuario.html.
- gestion_admin.html.
- registration/password_change_done.html.

La plantilla registration/login.html ya se reconoce como usada por template_name y no debe
tratarse como heredada.

### CSS candidatos

- configuraciones.css.
- legacy/01-base-preferencias.css hasta legacy/10-refresh-oscuro-paginas.css.
- logins.css.
- registers.css.
- registros.css.
- test.css.

Estos archivos son candidatos estáticos, no eliminaciones aprobadas. styles.css importa
parte del legado y debe conservarse hasta completar la revisión visual y de referencias.

### JavaScript

No se detectaron módulos JavaScript sin referencia estática. La carga actual queda cubierta
por app_shell.html, los bloques específicos de las páginas y los componentes existentes.

### Consultas prioritarias

El auditor encontró consultas de lectura dentro de bucles en:

- Principal/view_modules/acudientes.py, líneas 25, 28, 29 y 35.
- Principal/services/importacion_matriculas.py, líneas 89 y 105.
- Principal/services/avisos_academicos.py, línea 29.
- Principal/services/repasos_espaciados.py, líneas 19 y 24.
- Principal/view_modules/consentimientos.py, línea 59.
- Principal/view_modules/vocacional.py, líneas 41 y 71.
- Principal/view_modules/admin_escolar.py, línea 182.
- Varias plantillas con relaciones anidadas dentro de for.

El resultado es heurístico. Antes de corregirlo se debe medir cada flujo con
CaptureQueriesContext y agregar select_related/prefetch_related solamente donde exista
un aumento real de consultas.

## URLs

La aplicación tiene dos niveles de enrutamiento:

- ProyectoDeGrado/urls.py: healthz, readyz, admin y accounts.
- Principal/urls.py: dashboard, evaluaciones, simulacros, banco de preguntas, gestión,
  privacidad, predicción y portal académico.

Se detectó deuda de nomenclatura:

- Rutas antiguas en camelCase o snake_case conviven con rutas nuevas kebab-case.
- accounts/login/ y accounts/password_change/ se declaran antes de incluir
  django.contrib.auth.urls, por lo que existe una doble fuente de rutas potencial.
- Principal/views.py y Principal/management_views.py mantienen fachadas para compatibilidad.

El auditor agrupa automáticamente patrones y nombres duplicados, además de nombres
definidos que no tienen una referencia estática detectable.

## Consultas potencialmente repetidas

El caso más claro para revisión es Principal/view_modules/acudientes.py:

- Se recorre cada vínculo familiar.
- Dentro del bucle se consulta la matrícula activa.
- Dentro del mismo bucle se consultan los últimos intentos.
- Dentro del mismo bucle se consulta el plan semanal.
- Dentro del mismo bucle se cuenta ActividadAsignada pendiente.

Esto puede convertirse en N+1 cuando un acudiente tiene varios estudiantes. No se modifica
en esta fase; la corrección debe diseñarse con select_related, prefetch_related y consultas
agregadas, acompañada de una prueba de número de consultas.

También se revisan relaciones anidadas dentro de bucles de plantilla. El resultado del
auditor es heurístico y requiere confirmación con CaptureQueriesContext o Django Debug
Toolbar antes de optimizar.

## Cobertura

El workflow histórico de main ejecutaba las pruebas Django, pero no publicaba cobertura.
Por eso no existía una línea base medible en el repositorio.

La auditoría agrega un workflow separado que:

- Instala coverage.
- Ejecuta la suite de Principal.
- Usa PostgreSQL 16.
- Publica coverage report -m.
- Publica el HTML de cobertura como artefacto.
- No cambia la ejecución normal de main.

La cifra de cobertura se incorpora después de finalizar el workflow; no se inventa ni se
estima a partir del número de pruebas.

## PostgreSQL

La validación de esta fase usa un servicio PostgreSQL efímero en GitHub Actions. Esto
permite detectar diferencias que SQLite no revela, especialmente en:

- Migraciones.
- Restricciones.
- Consultas relacionadas.
- Tipos y transacciones.
- Compatibilidad con la configuración de producción.

La base es exclusiva de CI y no contiene datos reales.

## Resultado esperado de cierre

La Fase 1 se considera cerrada cuando:

- El auditor estático compila y genera su artefacto.
- La suite Django termina sobre PostgreSQL.
- La cobertura queda publicada con fecha y commit.
- Los candidatos heredados quedan documentados.
- Las consultas potencialmente repetidas quedan listadas.
- No se elimina ningún archivo ni se cambia el comportamiento de la aplicación.

La siguiente fase podrá ocuparse de la separación de formularios de perfil y de la
optimización de consultas, utilizando este inventario como línea base.
