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
