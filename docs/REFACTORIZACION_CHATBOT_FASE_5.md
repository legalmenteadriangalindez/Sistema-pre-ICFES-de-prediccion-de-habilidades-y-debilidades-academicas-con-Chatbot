# Fase 5 — Arquitectura de memoria del chatbot Pre-ICFES

## Objetivo

Se mantuvo `ModernMemoryManager` en su ruta original
`Principal/IA/LangGraph/graph_chatbot/memory_manager.py`, pero ahora es
una **fachada de ~65 líneas** que combina servicios especializados.
No cambian las URLs, permisos, mensajes de chat, comandos Django, esquema
de los registros JSON ni las tablas SQLite. La lógica de LangGraph
continúa en `chatbot.py`.

| Módulo | Responsabilidad |
| --- | --- |
| `conversation_store.py` | Metadatos de conversaciones, títulos, borrado y recuentos |
| `json_storage.py` | JSON privado con escritura atómica y sin truncar el original |
| `vector_memory.py` | ChromaDB y embeddings de HuggingFace para guardar/buscar |
| `memory_extraction.py` | Recuerdos extraídos por Ollama con fallback de reglas |
| `cognitive_profiles.py` | Historial de aprendizaje y perfiles cognitivos |
| `external_resources.py` | Búsqueda opcional de videos y enlaces |
| `memory_manager.py` | API estable: `ModernMemoryManager` y `UserManager` |

## Datos y compatibilidad

Se mantienen los mismos archivos por usuario bajo
`ProyectoDeGrado/DATABASES/USERS/<id>/`:
`chats_meta.json`, `cognitive_profile.json`, `chroma_db/`.
El checkpoint de LangGraph sigue en `langgraph_memory.db`.

Los métodos públicos `get_user_chats`, `create_new_chat`,
`update_chat_metadata`, `delete_chat`, `search_vector_memory`,
`save_memory_vectorial`, `build_cognitive_profile` y
`extract_and_store_memories` siguen disponibles. Las pruebas de la
fase 4 mantienen el comportamiento de la fachada y las rutas existentes.

Se usa `os.replace` para completar escrituras JSON: si un guardado
falla, el archivo previo permanece. Los perfiles antiguos de lista se
conservan y un perfil en forma de objeto se migra a lista al añadir uno
nuevo. Un archivo JSON corrupto se reporta sin sobrescribirlo.

## Errores Ollama y ChromaDB

- **Chroma no inicia:** las memorias vectoriales devuelven valores
  vacíos y el chatbot puede seguir funcionando sin recuerdos previos.
- **Chroma falla al guardar o buscar:** no se interrumpe la conversación;
  se registra un evento técnico sin mensajes personales.
- **Ollama no disponible:** el título tiene fallback al comienzo de la
  pregunta; la extracción pasa a reglas sencillas; el perfil cognitivo
  devuelve `None` si no puede generarse o parsearse. No se inventan
  niveles, notas ni errores del estudiante.
- **Ollama falla al responder el chat:** la interfaz recibe un mensaje
  controlado sin exponer prompts, rutas o excepciones internas.
- **JSON corrupto / disco lleno:** no se borra el archivo previo ni se
  interrumpe una lectura sin manejo de errores.

La memoria vectorial usa **el mismo modelo de embeddings** de HuggingFace
en escritura (`Chroma.add_texts`) y lectura
(`Chroma.similarity_search`). Así evita que el acceso directo a
`chromadb.Collection` use un modelo de embeddings diferente.

## Logs y privacidad

Se retiraron los `print()` de memoria y del flujo de respuesta de
chat. Los eventos se registran mediante `logging`, por ejemplo:
`chroma_search_failed`, `memory_extraction_llm_failed` y
`chat_inference_failed`, con metadatos técnicos
`component`/`error_type`. No se registran el texto de la conversación,
las respuestas del LLM, el correo o los perfiles cognitivos.

## Pruebas

`Principal/test_memoria_modular.py` incluye pruebas simuladas de
persistencia JSON, compatibilidad de API, fallos de Chroma en
inicialización/lectura/escritura, Ollama desconectado, salida cognitiva
inválida, y error de chat seguro. No necesitan instalar ni ejecutar los
modelos de HuggingFace u Ollama para hacer llamadas de inferencia.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_memoria_modular -v 2
python manage.py test Principal
```

GitHub Actions ejecuta además JavaScript y CSS. Se requiere que
todos los trabajos sean verdes antes de fusionar a `main`.

**Pendiente de comprobación manual:** grabación de audio real, acceso
al servicio Ollama local con el modelo configurado, uso de una colección
Chroma existente y verificación de conversaciones en navegador.
