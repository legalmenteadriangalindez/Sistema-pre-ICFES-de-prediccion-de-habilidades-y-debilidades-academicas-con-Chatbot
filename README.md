# Sistema Pre-ICFES con chatbot y cuestionarios

Aplicación Django para gestión académica, creación de cuestionarios con Ollama/Llama 3 y chatbot con memoria conversacional.

## Componentes activos

- **CRUD y autenticación:** `Principal/views.py`, `Principal/forms.py`, `Principal/models.py`, `Principal/urls.py` y plantillas correspondientes.
- **Cuestionarios:** `Principal/services/gestion_view_test.py` → `Principal/IA/LangGraph/graph.py` → `nodes.py` → `Principal/services/gestion_prompts.py` → `Principal/IA/chains.py` → `llm.py` y `prompts.py`.
- **Chatbot actual:** `Principal/IA/LangGraph/graph_chatbot/chatbot.py`, `memory_manager.py` y `states.py`; persiste historial y memorias por usuario.
- **Audio y archivos:** `Principal/services/audio.py`, `files.py`, `Principal/IA/processorAudio.py`, conectados al formulario de `home()`.

## Qué se retiró

Grafo de demostración, grafos antiguos del chatbot, RAG experimental no conectado, prototipo HTML alternativo del test, cachés compiladas y utilidades antiguas de memoria. Se mantienen las rutas CRUD, modelos, migraciones, plantillas en uso y datos existentes.

## Verificación manual

1. Prepara un entorno Python con dependencias compatibles de Django, LangChain, LangGraph, Chroma, audio y Ollama; las versiones deben documentarse y fijarse en una fase posterior.
2. Inicia Ollama con los modelos indicados en `Principal/IA/llm.py`.
3. Ejecuta `python manage.py check` y `python manage.py test`.
4. Comprueba registro, inicio de sesión, chat nuevo y existente, generación de cuestionarios, recomendaciones y CRUD usando datos de prueba.

## Importante antes de producción

El repositorio original ya tenía `db.sqlite3`, documentos en `media/` y bases de conversación en `ProyectoDeGrado/DATABASES/USERS/`. Esta limpieza **no los borra** para no perder datos. `.gitignore` solo impide nuevas incorporaciones de archivos sin seguimiento: **no elimina archivos ya versionados ni su historial**. Haz una copia de seguridad, revisa si contienen datos personales y prepara una retirada segura del repositorio/historial si es necesaria.

No publicar con `DEBUG=True`, secretos incrustados, operaciones administrativas sin control de roles ni eliminaciones por GET. Esta limpieza es **estática** y requiere pruebas locales antes de fusionarla.
