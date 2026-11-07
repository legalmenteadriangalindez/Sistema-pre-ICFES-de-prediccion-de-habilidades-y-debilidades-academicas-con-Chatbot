# Fase 8 — Responsabilidades del chatbot y sincronización académica

## Alcance

La vista `Principal/view_modules/chatbot.py` mantiene el nombre público
`home(request, *, render_func=render)` y las URL de la fase 4, pero ahora
se ocupa únicamente de **validar el rol, elegir el hilo y coordinar**.
El HTML, los archivos JS/CSS y la lógica de Django que usan otras pantallas
no cambian. No hay migraciones ni cambios de base de datos.

| Archivo | Responsabilidad |
| --- | --- |
| `view_modules/chatbot.py` | Enrutamiento y autenticación por roles |
| `services/tutor_chat_page.py` | Consultas GET, estadísticas académicas e historial sin escrituras |
| `services/tutor_chat_actions.py` | Acciones POST: conversación, crear/eliminar hilo, PDF y audio |
| `services/tutor_profile_sync.py` | Sincronización académica transaccional posterior a una respuesta exitosa |
| `IA/LangGraph/graph_chatbot/chatbot.py` | Grafo con extracción de recuerdos de contrato booleano |
| `services/services_view_home.py` | Ayudantes históricos de modelos sin `print()` de depuración |

## Antes y después

Antes, la portada `home()` sincronizaba `PerfilPedagogico` y
`AnalisisCognitivo` si encontraba un perfil cognitivo en JSON,
**incluso al recibir una petición GET**. Esto escribía datos académicos
cada vez que el alumno abría o recargaba la vista.

Ahora GET prepara y renderiza los datos sin llamar a servicios que
modifiquen esos modelos. La sincronización solamente se ejecuta
después de que un mensaje POST obtenga `resultado["success"] == True`.
Se conserva el formato del perfil JSON y los valores anteriores
de ritmo/estilo por compatibilidad. La función ignora perfiles incompletos
o identificados como pertenecientes a otro usuario. Se utiliza
`transaction.atomic()` para evitar actualizaciones parciales.
Si falla la sincronización o el almacenamiento de perfiles, el
mensaje generado puede seguir mostrándose sin exponer el error técnico.

La ruta `Principal.views.home` continúa con la misma fachada, de forma
que las pruebas y mocks que dependen de `Principal.views.render` y
`Principal.views.chatbotManager.get_chatbot` siguen funcionando.
Las acciones `delete_chat`, `borrarHistorial` y `nuevo_chat` conservan
su contrato, los UUID, el estado de sesión, la validación de PDF/audio
y las claves de contexto originales de `home.html`.

## Contrato de recuerdos

`MemoryExtractionMixin.extract_and_store_memories()` devuelve un
**booleano** e internamente guarda una memoria válida. El nodo de
LangGraph no debe convertir ese booleano a lista ni volver a llamar
a `save_memory_vectorial()`. La nueva función
`extraer_y_guardar_recuerdo()` realiza un único intento por mensaje,
marca `last_memory_extraction` y admite reintento ante una excepción
imprevista. No registra texto de estudiante en logs técnicos.

## Pruebas de regresión

`Principal/test_chatbot_fase8.py` contiene once tests para:

- Contrato booleano y ausencia de segunda escritura vectorial.
- Detección de repetición del mismo mensaje.
- Errores de memoria que no filtran contenido privado.
- GET sin escrituras académicas, incluso tras recargar.
- POST exitoso con actualización y sesión del mismo hilo.
- POST fallido sin actualización de perfil.
- Transacción y recuperación ante errores de base de datos.
- Ignorar perfiles JSON de terceros o incompletos.

GitHub Actions verifica estos tests junto con los anteriores, Ruff/Black,
ESLint, Stylelint y Playwright Chromium, antes de fusionar.

Comprobación local:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_chatbot_fase8 -v 2
python manage.py test Principal
```

La fase no equivale a un ensayo manual con Ollama real. También se debe
comprobar localmente la grabación, la carga PDF, la persistencia de
historial Chroma y los perfiles por usuario.
