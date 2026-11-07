# Cierre de preparación técnica para producción — 2026

Esta entrega **no significa que el Pre-ICFES esté publicado para menores ni
que varias instituciones puedan compartir una instancia**. La entrega configura
los requisitos técnicos verificables y corrige la integración de PDF/audio.

## Cambios funcionales

### Tutor PDF y audio

- PDF: admite archivos válidos de hasta 10 MB (regla previa), un máximo
  de 25 páginas y 2.800 caracteres legibles para el contexto del LLM.
  Valida extensión y cabecera y usa `pypdf`. Un PDF escaneado sin capa
  textual o protegido se rechaza con explicación; **no se ejecuta OCR**.
  La ruta de almacenamiento sigue siendo privada, sin URL pública.
- La extracción se usa como **material de contexto**, no como instrucciones
  para el modelo. El texto de PDF no se guarda como mensaje humano de la
  conversación, aunque el modelo puede procesarlo durante la petición.
  No se garantiza que toda respuesta de un LLM sea correcta.
- Audio: tras transcribir mediante Whisper local, la transcripción pasa
  efectivamente a la conversación, incluso sin pregunta escrita.
  Whisper y FFmpeg requieren instalaciones independientes y pruebas reales.
- En ambos casos se comprueba antes el consentimiento del acudiente
  cuando el usuario es menor, igual que para mensajes escritos.

### Producción técnica

- `DATABASE_URL` para PostgreSQL obligatorio en producción. No se
  permite publicar la aplicación en producción con SQLite efímera.
- `DJANGO_DATA_ROOT` debe ser una ruta absoluta persistente; contiene
  `users/` (LangGraph, ChromaDB, perfiles), `uploads/`, `media/` y
  `prediccion/modelo.json`. **Se debe migrar con respaldo el almacenamiento
  previo** antes de apuntar a esas rutas nuevas.
- WhiteNoise y `collectstatic` sirven CSS/JS; Gunicorn ejecuta Django.
- `/healthz/` verifica el proceso web y `/readyz/` la conexión a BD.
  No divulgan credenciales, nombres ni datos de estudiantes.
- `python manage.py auditar_piloto --modelo` informa requisitos y
  suficiencia de datos sin entrenar ni publicar modelos.
- `DJANGO_MULTIINSTITUCION=true` se rechaza explícitamente. Falta un
  diseño y una auditoría profunda de las consultas, matrículas, roles,
  ficheros, historiales, predicción y memoria para evitar fugas entre
  colegios. **No habilitar varios centros en la misma instalación**.

## Variables de entorno imprescindibles

En la instancia de producción, definir:
- `DJANGO_ENV=production`
- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY`: clave generada segura, nunca subirla a GitHub
- `DATABASE_URL`: cadena interna del PostgreSQL persistente
- `DJANGO_ALLOWED_HOSTS`: dominio real de la aplicación
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origen HTTPS completo del dominio
- `DJANGO_DATA_ROOT`: volumen persistente montado, ruta absoluta
- `DJANGO_TRUST_PROXY_SSL_HEADER=true` solo detrás del proxy HTTPS que sanee ese header
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`: motor accesible y autorizado; nunca
  apuntar indiscriminadamente a un servidor público sin TLS y privacidad.

No adjuntar archivos de estudiantes a GitHub Actions ni a una instancia
de demostración abierta.

## Blueprint Render

`render.yaml` describe un servicio Python, Gunicorn, PostgreSQL y un
disco privado persistente. **La infraestructura especificada es de pago**.
No se ha ejecutado ningún aprovisionamiento ni aprobado un costo.
La conexión de Render disponible no tenía un servicio de Pre-ICFES ni
PostgreSQL existente en la verificación inicial.

Para el despliegue real:
1. Revisar los precios concretos de PostgreSQL, CPU y disco en Render.
2. Preparar una instancia de **una sola institución** con datos ficticios.
3. Configurar `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
   el motor IA y permisos de acceso a datos.
4. Aprobar el plan de infraestructura y crear la BD/servicio.
5. Realizar backup verificable, migrar y restaurar los archivos de memoria
   privados a `DJANGO_DATA_ROOT`, sin subirlos al repositorio.
6. Ejecutar `python manage.py check --deploy`, `auditar_piloto --modelo`,
   `auditar_cierre --ollama` (solo si Ollama está en localhost) y la
   batería de pruebas con datos ficticios.
7. Verificar `/readyz/` y luego los flujos de navegador, roles,
   correo, adjuntos reales, carga alta, recuperación y políticas de datos.
8. En GitHub, habilitar Rulesets para proteger `main` (se requieren permisos
   administrativos).

## Comandos para el proyecto local

Antes de actualizar: respaldar PostgreSQL/SQLite y las carpetas de
chats, Chroma, modelos y PDFs. Después:

```powershell
git pull origin main
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test Principal
python manage.py auditar_piloto --modelo
python manage.py runserver
```

Para audio real se requieren `requirements-audio.txt`, FFmpeg y
un motor Whisper compatible. No se descargan modelos en CI.

## Criterios pendientes para producción institucional

- Aislamiento multiinstitucional completo y pruebas entre colegios.
- Evaluación de validez de cuestionarios y predicción con datos reales
  consentidos; mejora pred/post descriptiva no demuestra causalidad.
- Revisión legal y organizacional de datos de menores, derechos de
  eliminación, retención de copias, backups, memorias y documentos.
- Pruebas reales de Ollama/Whisper, PDFs complejos, redes lentas y
  accesibilidad con usuarios.
- Recuperación de respaldos, monitoreo, alertas y costes del despliegue.
- Protección administrativa de `main` y aprobación del plan de Render.

**El paso a producción no se deduce de una suite verde de GitHub.**
