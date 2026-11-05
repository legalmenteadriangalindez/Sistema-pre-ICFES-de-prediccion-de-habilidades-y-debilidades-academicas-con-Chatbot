# Pre-ICFES

Aplicación web para preparación académica Saber 11, con gestión de estudiantes, evaluaciones, simulacros y tutor con IA.

## Arranque rápido

Requisitos: Python 3.12 o 3.13. El primer arranque crea el entorno virtual, instala las dependencias, crea `.env`, prepara una base SQLite vacía y levanta el sitio.

### Windows

1. Descarga y extrae el ZIP del repositorio, o clónalo con Git.
2. Instala Python 3.12 y activa la opción para agregarlo al `PATH`.
3. Haz doble clic en `run_local.bat`.
4. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

También puedes abrir PowerShell en la carpeta del proyecto y ejecutar `.\run_local.ps1`.

### macOS y Linux

1. Descarga y extrae el ZIP, o clona el repositorio.
2. Instala Python 3.12 o 3.13.
3. En la terminal, entra a la carpeta del proyecto y ejecuta:

   ```bash
   chmod +x run_local.sh
   ./run_local.sh
   ```

4. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

El servidor se detiene con `Ctrl+C`. La base de datos local y los archivos cargados se guardan dentro de la carpeta del proyecto y no se suben a Git.

## Qué prepara el script

- Crea el entorno aislado `.venv` e instala `requirements.txt`.
- Copia `.env.example` a `.env` solo si todavía no existe.
- Ejecuta las migraciones para crear `local.sqlite3`.
- Arranca Django en `127.0.0.1:8000`.

Al volver a ejecutarlo, no reinstala las dependencias mientras `requirements.txt` siga igual. No borres `.venv` si quieres conservarlas.

Para crear un usuario administrador, abre otra terminal en la carpeta del proyecto y ejecuta:

```bash
# Windows
.venv\Scripts\python manage.py createsuperuser

# macOS / Linux
.venv/bin/python manage.py createsuperuser
```

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
- **El tutor no responde:** instala/abre Ollama y confirma que `ollama list` muestre el modelo configurado en `.env`.
- **No aparece el correo de verificación:** revisa la terminal del servidor Django. En modo local el mensaje se imprime allí.
- **Error de FFmpeg:** confirma que instalaste FFmpeg para tu sistema y que `ffmpeg -version` funciona desde una terminal nueva.

## Datos del repositorio

Cada instalación nueva crea su propia `local.sqlite3`; no se distribuye una base de datos inicial. La carpeta `media/`, las memorias del tutor y los archivos `.env` quedan locales y están excluidos de Git.

Para descargar el código, usa **Code → Download ZIP** en GitHub. El ZIP de la rama `main` contiene el estado actual del proyecto, sin la historia de Git ni los datos locales de otras instalaciones. La solicitud cerrada #1 todavía puede mostrar referencias a commits anteriores. Si esos commits contenían datos personales, credenciales u otra información sensible, sigue la [guía oficial de GitHub para retirar datos sensibles](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository); GitHub Support evalúa estas solicitudes caso por caso.

## Reiniciar la base de datos y crear usuarios de prueba (desarrollo local)

Este proyecto utiliza SQLite en `local.sqlite3`. **No elimines la carpeta `Principal/migrations/`**: las 11 migraciones que contiene son necesarias para recrear las tablas.

### Copia limpia del proyecto

El ZIP preparado para pruebas **no incluye** la antigua `local.sqlite3`, la configuración privada `.env` ni los archivos `__pycache__`. Conserva el código, las migraciones, las vistas, los estilos y las dependencias del proyecto original.

**Windows, forma más fácil:** extrae el ZIP en una carpeta nueva y haz doble clic en `iniciar_pruebas.bat`. Ese archivo reutiliza el instalador de `run_local.bat`, crea la base SQLite con migraciones, carga los usuarios ficticios y abre el servidor en `http://127.0.0.1:8000/`. Necesitas Python 3.12 o 3.13 e Internet para instalar las dependencias la primera vez. Si usas la aplicación sin el motor de IA, algunas funciones de chatbot y generación de pruebas podrían requerir Ollama.

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
3. Vuelve a ejecutar `iniciar_pruebas.bat` (o `manage.py migrate`, luego `manage.py crear_usuarios_prueba`). Django construirá una base nueva sin recuperar la anterior.
4. **No borres ni regeneres las migraciones** para este procedimiento. La restauración de la base de datos anterior es posible si conservas `local.sqlite3.respaldo`.

Las pruebas automatizadas específicas para estas cuentas están en `Principal/test_usuarios_prueba.py`; puedes ejecutarlas con `python manage.py test Principal.test_usuarios_prueba` en el entorno con las dependencias instaladas.
