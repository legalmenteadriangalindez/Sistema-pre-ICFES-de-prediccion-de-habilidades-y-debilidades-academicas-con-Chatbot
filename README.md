# Pre-ICFES

Aplicación web para preparación académica Saber 11, con gestión de estudiantes, evaluaciones, simulacros y tutor con IA.

## Ejecución normal con Python (recomendada)

Requiere Python **3.12 o 3.13**. No necesitas ejecutar archivos `.bat` ni `.ps1` para iniciar el proyecto: utiliza los comandos habituales de Django en la terminal de VS Code, situada en la carpeta donde está `manage.py`.

### Primera ejecución

Si todavía no has instalado las dependencias, puedes crear y activar un entorno virtual (recomendado):

```powershell
python -m venv .venv
```

Actívalo en **CMD** con `.venv\Scripts\activate.bat`, o en **PowerShell** con `.\.venv\Scripts\Activate.ps1`. Si PowerShell bloquea el script, utiliza CMD o ejecuta `Set-ExecutionPolicy -Scope Process Bypass` solo en esa terminal y vuelve a activarlo.

Con el entorno activado, ejecuta:

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py crear_usuarios_prueba
python manage.py runserver
```

- `migrate` crea automáticamente `local.sqlite3` y todas las tablas a partir de las migraciones **existentes**.
- `crear_usuarios_prueba` agrega cinco cuentas ficticias con roles y perfiles para pruebas locales. **Opcional:** omite este comando si no quieres datos de demostración y crea cuentas mediante la aplicación o con `python manage.py createsuperuser`.
- `runserver` levanta el sitio en [http://127.0.0.1:8000/](http://127.0.0.1:8000/) y se detiene con `Ctrl+C`.

### Cada vez que vuelvas a abrir el proyecto

Activa el mismo entorno virtual en la terminal y ejecuta **únicamente**:

```powershell
python manage.py runserver
```

No es necesario volver a instalar dependencias ni recrear usuarios; tampoco se pierde la base de datos al detener el servidor. Cuando descargues cambios que incluyen migraciones nuevas, ejecuta `python manage.py migrate` una vez antes de iniciar. Si aparece `ModuleNotFoundError: No module named 'django'`, asegúrate de que el entorno esté activado e instala `requirements.txt` con ese mismo Python.

### Scripts auxiliares opcionales

Los archivos `run_local.bat`, `run_local.ps1`, `run_local.sh` e `iniciar_pruebas.bat` se conservan por compatibilidad, **pero no son necesarios**. El inicio habitual sigue siendo `python manage.py runserver`.


## Correcciones integradas de noviembre de 2026

- **Migración `0012` corregida:** primero elimina las restricciones de las tablas antiguas y después sus campos; así evita errores como `NewAsignacionDocente has no field named 'anio_lectivo'` y `Principal_curso.jornada_id` al preparar una base nueva.
- **Acceso según rol:** el administrador (`is_superuser` o rol `ADMIN`) que entra al inicio `/` es redirigido a `/admin_gestion_users/` antes de cargar el tutor de estudiantes. El inicio estudiantil sigue disponible para los usuarios ordinarios.
- **Usuarios ficticios:** `python manage.py crear_usuarios_prueba` crea cinco cuentas de desarrollo sin duplicarlas; no es un requisito para usar `python manage.py runserver`.
- **Respaldos privados:** se ignoran los archivos `*.sqlite3`, `*.respaldo-*` y `*.original.bak` para evitar subir bases y copias de migraciones a Git.

**Bases de datos existentes:** la migración `0012` elimina campos y modelos heredados; se probó el procedimiento sobre la base de desarrollo del proyecto, no como migración de datos históricos. Antes de aplicarla a una base con información real, respáldala y revisa el impacto de esos cambios. Si ya aplicaste `0012` en tu máquina con un archivo generado y corregido localmente, no necesitas recrear SQLite ni repetirla; conserva ese archivo y su respaldo al actualizar el código.


## Correcciones de regresión del chat y seguimiento (noviembre 2026)

- **Continuidad:** al crear la primera conversación el motor devuelve su UUID real; la interfaz lo conserva en la sesión y en el formulario. Al seguir preguntando se utiliza ese hilo, incluso después de recargar el inicio.
- **Eliminación de conversaciones:** borrar un chat elimina primero sus checkpoints y escrituras del almacenamiento SQLite de LangGraph mediante `SqliteSaver.delete_thread`, y después retira su entrada del listado. Si falla el borrado del checkpoint, el chat no se oculta como si se hubiese eliminado. «Vaciar conversación» elimina igualmente el estado del hilo y conserva su entrada en el listado.
- **Alcance del borrado:** la eliminación retira los registros activos de ese hilo, **pero no borra las memorias vectoriales transversales, los perfiles cognitivos o las copias de seguridad**, que tienen un ciclo de vida distinto. Tampoco garantiza que los bytes antiguos hayan sido purgados físicamente del archivo SQLite o su WAL. No describirlo como «olvido total» de datos personales.
- **Seguimiento:** `Simulacro: Integral ampliado` atribuye cada respuesta a su materia, igual que el modo integral básico.
- **Regresiones:** `Principal.test_regresiones_chat_y_demo` incluye 13 pruebas de flujos y de las cinco cuentas locales. Usan dobles de prueba para la IA; no descargan Ollama.

Para verificar en tu instalación:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal --verbosity 2
```

En GitHub Actions la misma batería se ejecuta con Python 3.12 en solicitudes de cambio y al actualizar `main`. Verifica que el resultado del workflow sea verde. Para validar respuestas reales de la IA, inicia Ollama con el modelo configurado y prueba una conversación de dos mensajes desde el navegador: los tests automatizados usan mocks y **no sustituyen esa comprobación manual**.

**Cuentas demo:** solo disponibles en desarrollo local; crea o verifica con `python manage.py crear_usuarios_prueba`. Nunca subas `local.sqlite3`, `.env` ni contraseñas de producción.

## Refactorización de memoria del chatbot — fase 5 (noviembre de 2026)

`ModernMemoryManager` se conserva como fachada compatible y se separa en
servicios de conversaciones JSON, ChromaDB, extracción de recuerdos, perfiles
cognitivos y recursos auxiliares. Escritura JSON atómica y embeddings
consistentes al leer/guardar. Sin conversaciones ni respuestas completas en
`print()`; los logs contienen solo eventos técnicos. Se añaden pruebas
de fallos simulados de Ollama, Chroma y disco sin conexión externa.

No cambia la base SQLite, las URLs ni los datos existentes.
Ver [arquitectura y pruebas de fase 5](docs/REFACTORIZACION_CHATBOT_FASE_5.md).

## Refactorización de vistas Django — fase 4 (noviembre de 2026)

Se separaron autenticación, chatbot, cuestionarios, perfiles, estudiantes,
orientación, seguimiento, docentes, acudientes y administración en módulos
propios de `Principal/view_modules/`. Las tres vistas monolíticas originales
ahora actúan como **fachadas de compatibilidad**, preservando rutas, nombres
públicos, decoradores de permisos y los puntos de mock de las pruebas. No
se cambiaron modelos, migraciones ni datos de alumnos.

Se añadieron pruebas de rutas, autenticación, imports y contratos históricos.
Consulta el [mapa de responsabilidades de la fase 4](docs/REFACTORIZACION_VISTAS_FASE_4.md).

## Refactorización de HTML y componentes — fase 3 (noviembre de 2026)

Se añadieron componentes Django en `Principal/templates/components/` para
tarjetas, avisos, métricas, campos, tablas y modales. Registro, gestión
administrativa, permisos docentes, plan semanal y predicción ahora reutilizan
esas piezas sin alterar los nombres de los formularios ni la lógica de las
vistas. Se añadieron pruebas de renderizado, seguridad, compatibilidad HTML
y accesibilidad básica. Las plantillas heredadas dudosas **no se borraron**:
se documentaron para revisión específica.

Consulta [mapa de componentes y revisión de HTML](docs/REFACTORIZACION_HTML_FASE_3.md).

## Refactorización de CSS — fase 2 (noviembre de 2026)

Se introdujo `design-tokens.css` como fuente común para colores,
tipografía, espacios, botones y sombras. Se corrigió la cascada en
`app_shell.html` para que los estilos específicos se carguen **después**
de las capas globales. Los archivos CSS comprimidos se formatearon y las
capas grandes se distribuyeron en módulos manteniendo el orden de reglas.
Se eliminaron cuatro `!important` redundantes, sin modificar las
excepciones necesarias de modo oscuro ni el comportamiento del simulacro.

Las hojas heredadas de Login y Registro siguen disponibles. GitHub Actions
agrega pruebas de sintaxis y cascada CSS con TinyCSS2, además de Node y Django.
Consulta [metodología y mapa CSS de fase 2](docs/REFACTORIZACION_CSS_FASE_2.md).

## Refactorización de JavaScript — fase 1 (noviembre de 2026)

Se separaron navegación, preferencias, confirmaciones, chat, micrófono y
filtros administrativos en módulos seguros para páginas sin esos controles.
Las preferencias existentes se conservan y los scripts específicos se cargan
solo donde se necesitan. Se retiraron `script.js` y cuatro archivos JS
vacíos, después de revisar referencias.

GitHub Actions ejecuta pruebas de Django **y** pruebas JavaScript Node sin
dependencias adicionales. Ver [documentación de la fase 1](docs/REFACTORIZACION_JS_FASE_1.md).

## Predicción académica evaluable (noviembre de 2026)

Se incorporó un **pipeline reproducible de aprendizaje automático**, pero **no se publica ningún resultado predictivo sin datos reales suficientes y evaluación aprobada**. No se han subido datos de estudiantes ni modelos entrenados al repositorio.

- Objetivo: clasificar si el **siguiente** intento de una materia obtendrá menos de **60 % de aciertos**, usando resultados anteriores, nunca respuestas futuras.
- Datos: registros de `IntentoEvaluacion` y `RespuestaEvaluacion` con al menos cinco preguntas por materia; se excluyen las cinco cuentas demo. No se usan nombre, edad, documento, sexo, dirección ni correo como variables.
- Mínimos para intentar entrenar: **40 estudiantes distintos, 150 ejemplos temporales, al menos 30 ejemplos de cada clase**. Se evalúa además la representación de las materias en el conjunto de prueba.
- Modelo: estandarización + regresión logística; división por **estudiantes completos** (25 % de alumnos solo para prueba), comparación con clase mayoritaria, métricas F1, precisión, recuperación, exactitud balanceada, AUC, Brier y matriz de confusión.
- Requisitos para publicar: mejora de al menos **0,05** de exactitud balanceada sobre la referencia y precisión y recuperación del riesgo de al menos **0,55**; únicamente aparecen áreas también validadas por separado.
- **Sin modelo válido:** la aplicación muestra “predicción aún no validada”, sin porcentajes inventados. Las predicciones aprobadas se expresan como sugerencias de práctica, no notas ni puntajes ICFES.
- El archivo JSON privado de coeficientes y métricas se conserva en `.local-data/prediccion/modelo.json`, ignorado por Git, y vence a los 180 días.

Comandos del administrador del servidor:

```powershell
python manage.py entrenar_prediccion
python manage.py entrenar_prediccion --entrenar
```

El primero audita sin entrenar; el segundo solo publica si pasa los controles. Páginas: `/prediccion-academica/` (estudiante) y `/gestion/validacion-prediccion/` (administrador). Consulta el diseño y las limitaciones en [Metodología predictiva](docs/PREDICCION_ACADEMICA.md).

## Seguimiento semanal persistente (noviembre de 2026)

La ruta **`/plan-semanal/`** permite crear un plan por estudiante y por semana (lunes a domingo), registrar las siete sesiones propuestas y comparar avances de las últimas ocho semanas. Es independiente de las tareas que asignan los docentes.

- **Persistencia real:** migración `0014_plan_estudio_semanal_persistente` con `PlanEstudioSemanal` y `SesionPlanSemanal`. Cada estudiante solo puede crear un plan por semana. Guardar de nuevo no duplica registros ni borra sesiones.
- **Seguimiento:** cada sesión permite registrar entre **1 y 480 minutos** y una nota opcional de hasta **500 caracteres**, editar el registro o volver a marcarlo como pendiente. Las semanas anteriores pueden consultarse pero no modificarse desde la interfaz.
- **Indicadores:** sesiones realizadas/pendientes, porcentaje de cumplimiento, minutos registrados frente a los planificados, historial de semanas con sus porcentajes. Los indicadores reflejan **autoregistros**, no tiempo supervisado ni calificaciones.
- **Personalización:** al crear la semana se usan las áreas y competencias medidas por las evaluaciones; sin respuestas se propone una rotación general. El plan se conserva como **instantánea**: los diagnósticos nuevos afectarán semanas futuras, no reescribirán sesiones históricas.
- **Privacidad:** las operaciones por POST validan estudiante autenticado y semana actual. Los acudientes formalmente vinculados solo pueden ver el resumen de la semana actual. La exportación de datos personales incluye planes y sesiones propios.
- **No depende de Ollama** y no cambia las tablas existentes de matrículas, evaluaciones o asignaciones del docente.

Antes de ejecutar esta versión haz respaldo de `local.sqlite3` y aplica la migración `0014`:

```powershell
git pull origin main
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal
python manage.py runserver
```

Para probarlo entra como `estudiante_ana` (en un entorno local preparado con los usuarios demo), abre `/plan-semanal/`, crea el plan, registra una sesión, comprueba el porcentaje y revisa el historial. La cuenta `acudiente_demo` podrá consultar el resumen del estudiante vinculado. No debes volver a crear la base de datos ni modificar la migración 0012.

## Seguridad y privacidad (noviembre de 2026)

**Cambios de esta versión (requiere migración `0013`):**

- **Permisos docentes:** los administradores conceden y revocan permisos en `/gestion/asignaciones-docentes/`. El panel `/panel-docente/` muestra **solo las matrículas** de los pares curso/año autorizados. Los POST también validan permisos, incluso si alguien envía identificadores manipulados. Un docente sin asignaciones no puede crear ni asignar actividades; el comando de usuarios demo otorga únicamente 11A/2026 a `docente_demo`. El control es por curso y año, **no sustituye un aislamiento multicolegio**.
- **Archivos privados:** adjuntos del tutor bajo `.private-media/<id de usuario>/pdfs|audios/`, fuera de MEDIA_URL. Extensiones/cabeceras y límites validados: **PDF de hasta 10 MiB** y **audio de hasta 25 MiB** (WAV, MP3, OGG, OPUS, M4A y WEBM). Se asignan nombres aleatorios para evitar sobreescritura. Los formatos de Office no están admitidos en el formulario.
- **Medios antiguos:** se deshabilitó servir `MEDIA_URL` desde Django en modo desarrollo. Los archivos PDF/audio almacenados antes de esta actualización pueden permanecer en `media/`; **no se movieron ni eliminaron automáticamente** porque no existe un vínculo fiable con el propietario. Requieren un plan de migración y limpieza manual.
- **Privacidad:** la ruta autenticada `/privacidad/` da acceso a `/privacidad/exportar/`: un JSON sin caché con **solo datos de perfil y registros académicos propios**, sin contraseña ni información de usuarios ajenos. **No es una exportación completa**: quedan fuera datos de ChromaDB/LangGraph, archivos adjuntos y copias de seguridad.
- **Borrado de cuentas desde administración:** elimina cuenta y relaciones Django en transacción, y después del commit intenta limpiar las carpetas privadas nuevas y la carpeta de conversaciones de esa cuenta. Si falla la limpieza se registra el error en logs para intervención; los backups y medios legacy deben gestionarse aparte. Eliminar una persona vinculada ahora elimina también su cuenta, para no dejar accesos huérfanos.
- **Pruebas:** `Principal.test_seguridad_privacidad` cubre formatos inválidos, permisos docentes revocados, acceso cruzado, exportación y limpieza. No se accede a bases locales en GitHub Actions.

**Después de actualizar el código y antes de levantar la app:**

```powershell
python manage.py migrate
python manage.py check
python manage.py test Principal
python manage.py runserver
```

Haz copia de `local.sqlite3` y de las carpetas de datos personales antes de ejecutar la migración. No elimines ni regeneres la migración `0012` ya aplicada en tu instalación. Verifica las asignaciones docentes existentes desde el panel de administración después de migrar: el nuevo modelo inicia vacío en instalaciones reales, por diseño de seguridad.

## Nuevos flujos académicos (noviembre de 2026)

La aplicación incorpora funcionalidades sin añadir tablas nuevas:

- **Orientación vocacional:** `/orientacion-vocacional/` (12 afirmaciones; recomendaciones orientativas guardadas para estudiantes con matrícula).
- **Comparador de carreras:** `/compararCarreras/` (hasta tres carreras del catálogo).
- **Diagnóstico por competencias:** `/diagnostico-academico/` (resultados observados, sin afirmar predicciones de IA).
- **Plan semanal:** `/plan-semanal/` (propuestas basadas en áreas por reforzar).
- **Docentes:** `/panel-docente/` (crear y asignar actividades; se requiere rol DOCENTE).
- **Acudientes:** `/acudiente/` (únicamente estudiantes formalmente vinculados).
- **Simulacros:** nueva modalidad opcional «Integral ampliado» con 50 preguntas de práctica.

Consulta [GUIA-FUNCIONES-2026.md](GUIA-FUNCIONES-2026.md) para detalles, límites y comandos de pruebas.

**Límites actuales:** no hay un modelo predictivo ML validado, ni vínculo docente–curso para restringir acciones en despliegues multiinstitución. Estas funciones no requieren Ollama, pero el tutor con IA y los cuestionarios generados sí requieren el modelo configurado. Las 50 preguntas no constituyen un examen oficial del ICFES.

## Funciones opcionales

### Chat y generación con IA

La aplicación web funciona sin Ollama, pero las respuestas del tutor y la generación de cuestionarios necesitan Ollama y el modelo configurado. Instala Ollama desde [ollama.com/download](https://ollama.com/download), deja el servicio iniciado y descarga el modelo:

```bash
ollama pull llama3:8b
```

La primera descarga del modelo puede tardar y ocupa espacio. En el primer uso del tutor también se descarga el modelo pequeño de embeddings. Si ya usas otro modelo, edita `OLLAMA_MODEL` en `.env`.

### Verificación de correo

En modo local no hace falta configurar un servicio de correo. Al registrarte, el enlace de verificación se imprime en la terminal donde está ejecutándose Django. Para enviar correos reales, configura `BREVO_API_KEY` y `BREVO_SENDER_EMAIL` en `.env`.

### Transcripción de audio

La transcripción necesita instalar el paquete opcional y FFmpeg:

```bash
python -m pip install -r requirements-audio.txt
```

Instala FFmpeg en el sistema y confirma que el comando `ffmpeg` esté disponible en `PATH`. La primera transcripción descarga el modelo de Whisper indicado por `WHISPER_MODEL` en `.env`.

## Instalación manual

Si prefieres preparar el entorno por tu cuenta:

```bash
python -m venv .venv
```

Activa el entorno (`.venv\Scripts\activate` en Windows o `source .venv/bin/activate` en macOS/Linux), luego:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copia `.env.example` a `.env`, prepara la base de datos y arranca:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Configuración

Los valores locales están en `.env`, que está excluido de Git. Las variables principales son:

| Variable | Uso |
| --- | --- |
| `DJANGO_DB_PATH` | Archivo SQLite; por defecto `local.sqlite3`. |
| `DJANGO_SECRET_KEY` | Clave de Django. El valor del ejemplo es solo para desarrollo. |
| `OLLAMA_BASE_URL` | Dirección del servicio Ollama; por defecto `http://127.0.0.1:11434`. |
| `OLLAMA_MODEL` | Modelo local; por defecto `llama3:8b`. |
| `WHISPER_MODEL` | Modelo opcional de audio; por defecto `base`. |
| `BREVO_API_KEY`, `BREVO_SENDER_EMAIL` | Credenciales opcionales para correo real. |

No uses los valores de `.env.example` en producción. Para desplegar el sistema hacen falta claves y dominios propios, `DEBUG=False` y una base de datos configurada para ese entorno.

## Si algo falla

- **`python` no se reconoce:** instala Python 3.12 y reinicia la terminal. En Windows también puedes ejecutar `py -3.12`.
- **No se pueden instalar dependencias:** confirma que tienes conexión a Internet y espacio disponible. El conjunto de IA instala bibliotecas de aprendizaje automático y puede tomar varios minutos.
- **El tutor no responde:** instala/abre Ollama, verifica que el servidor esté disponible con `ollama list` y descarga el modelo configurado en `.env` (por defecto `ollama pull llama3:8b`). El error `model 'llama3:8b' not found (404)` indica que falta descargar ese modelo; no es un fallo de Django.
- **No aparece el correo de verificación:** revisa la terminal del servidor Django. En modo local el mensaje se imprime allí.
- **Error de FFmpeg:** confirma que instalaste FFmpeg para tu sistema y que `ffmpeg -version` funciona desde una terminal nueva.

## Datos del repositorio

Cada instalación nueva crea su propia `local.sqlite3`; no se distribuye una base de datos inicial. La carpeta `media/`, las memorias del tutor y los archivos `.env` quedan locales y están excluidos de Git.

Para descargar el código, usa **Code → Download ZIP** en GitHub. El ZIP de la rama `main` contiene el estado actual del proyecto, sin la historia de Git ni los datos locales de otras instalaciones. La solicitud cerrada #1 todavía puede mostrar referencias a commits anteriores. Si esos commits contenían datos personales, credenciales u otra información sensible, sigue la [guía oficial de GitHub para retirar datos sensibles](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository); GitHub Support evalúa estas solicitudes caso por caso.

## Reiniciar la base de datos y crear usuarios de prueba (desarrollo local)

Este proyecto utiliza SQLite en `local.sqlite3`. **No elimines la carpeta `Principal/migrations/`**: sus 12 migraciones (`0001`–`0012`) son necesarias para recrear las tablas.

### Copia limpia del proyecto

El ZIP preparado para pruebas **no incluye** la antigua `local.sqlite3`, la configuración privada `.env` ni los archivos `__pycache__`. Conserva el código, las migraciones, las vistas, los estilos y las dependencias del proyecto original.

**Inicio recomendado:** usa los cuatro comandos de la sección «Ejecución normal con Python»; el archivo `iniciar_pruebas.bat` queda como una alternativa opcional para Windows. Si usas la aplicación sin el motor de IA, algunas funciones de chatbot y generación de pruebas podrían requerir Ollama.

**Windows, con terminal** (tras instalar las dependencias):

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py crear_usuarios_prueba
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

**macOS/Linux** (tras ejecutar `./run_local.sh` para preparar el entorno, o instalar las dependencias manualmente):

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py crear_usuarios_prueba
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

### Cuentas ficticias de demostración

| Usuario | Rol | Contraseña inicial |
| --- | --- | --- |
| `admin_demo` | Administrador (superusuario Django) | `PreICFES2026!Demo` |
| `estudiante_ana` | Estudiante | `PreICFES2026!Demo` |
| `estudiante_luis` | Estudiante | `PreICFES2026!Demo` |
| `acudiente_demo` | Acudiente | `PreICFES2026!Demo` |
| `docente_demo` | Docente | `PreICFES2026!Demo` |

Los usuarios están **activos** y pueden iniciar sesión sin verificación de correo. Se crean los perfiles, las personas y los sexos de prueba. Además, los dos estudiantes se matriculan en `Undécimo / 11A / 2026` y quedan relacionados con el acudiente de prueba. El rol `DOCENTE` no implica un módulo docente separado: es el rol disponible para probar el acceso existente. Todos los correos utilizan `example.test` y no pertenecen a personas reales.

- Inicio de sesión: `http://127.0.0.1:8000/accounts/login/`
- Administración de Django: `http://127.0.0.1:8000/admin/` (entrar como `admin_demo`).
- Para restablecer las contraseñas demo si vuelves a olvidarlas: `.\.venv\Scripts\python.exe manage.py crear_usuarios_prueba --resetear-claves`.
- Para cambiar la contraseña del administrador sin tocar las otras: `.\.venv\Scripts\python.exe manage.py changepassword admin_demo`.
- Si vuelves a ejecutar el comando sin `--resetear-claves`, no duplica las cuentas ni les cambia sus contraseñas.
- Opcional: establece la variable de entorno `PREICFES_DEMO_PASSWORD` con una contraseña de al menos 12 caracteres para usar otra clave de demostración. Esta función está bloqueada cuando `DEBUG=False` o `DJANGO_ENV=production`.

**No utilices estas contraseñas públicas ni el usuario `admin_demo` en servidores accesibles por Internet.** El comando solo sirve para desarrollo en tu computador.

### Si deseas borrar nuevamente los datos locales

1. Detén Django y haz una copia de tu carpeta, especialmente si tienes evaluaciones o datos que quieres conservar.
2. En Windows PowerShell, dentro del proyecto, usa `Rename-Item .\local.sqlite3 local.sqlite3.respaldo` (o mueve el archivo a una carpeta segura) si existe. No necesitas saber ninguna contraseña para hacerlo.
3. Ejecuta `python manage.py migrate` y `python manage.py crear_usuarios_prueba`; después inicia con `python manage.py runserver`. Django construirá una base nueva sin recuperar la anterior.
4. **No borres ni regeneres las migraciones** para este procedimiento. La restauración de la base de datos anterior es posible si conservas `local.sqlite3.respaldo`.

Las pruebas automatizadas están en `Principal/test_usuarios_prueba.py` y `Principal/test_redireccion_roles.py`; ejecútalas con `python manage.py test Principal.test_usuarios_prueba Principal.test_redireccion_roles` desde el entorno con las dependencias instaladas.
