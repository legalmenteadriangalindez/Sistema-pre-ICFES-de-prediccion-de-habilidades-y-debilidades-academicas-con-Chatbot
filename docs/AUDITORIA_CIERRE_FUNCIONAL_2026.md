# Auditoría de cierre Pre-ICFES — noviembre 2026

## Alcance y límites verificables

Este cambio **no altera las evaluaciones, el chatbot, los modelos ni las migraciones**.
Agrega una batería integrada Django para sesiones, persistencia, archivos,
roles, historial y privacidad. Reutiliza los tests existentes de predicción,
memoria LangGraph y permisos. GitHub Actions ejecuta tests y Playwright
Chromium con datos **sintéticos**; no se envían datos reales a CI.

**No declarar funcionalidad 100 % completa únicamente porque CI aprueba**:
los tests de Ollama y audio real requieren el servidor/los modelos instalados
en el computador del operador. Un PDF que se sube y se guarda de forma segura
**no implica** que su contenido se haya analizado por el tutor. La versión
actual guarda PDF privado; el chat procesa un prompt por separado.
La versión actual transcribe audio después de la rama del mensaje;
una carga de audio sin prompt no envía automáticamente su transcripción
a la conversación. Son limitaciones funcionales documentadas y se
deben diseñar/priorizar separadamente antes de afirmar que el chat procesa
automáticamente esos adjuntos.

## 1. Chatbot real, conversación, adjuntos y memoria

Pruebas automatizadas: `Principal.test_cierre_integral`,
`Principal.test_regresiones_chat_y_demo`,
`Principal.test_memoria_modular`,
`Principal.test_seguridad_privacidad`.
Verifican el hilo y la sesión tras recarga, envío y validación de PDF,
invocación del transcriptor, directorios privados, checkpoint y memoria con
mocks. **No prueban inferencia real ni transcripción real**.

### Pruebas locales imprescindibles (solo con datos ficticios)

1. Preparar un entorno de desarrollo aislado y guardar respaldos antes de migrar.
2. Iniciar Ollama y verificar modelo: `ollama list`.
3. Ejecutar `python manage.py auditar_cierre --ollama`. Envía una pregunta
   matemática **sintética** exclusivamente al Ollama local; no identifica
   estudiantes, no crea chats y no modifica la base.
4. Iniciar Django, entrar como estudiante de prueba, preguntar algo y
   verificar respuesta. Recargar; comprobar que el UUID/hilo se conserva.
   Realizar una segunda pregunta y revisar el historial. Cerrar sesión,
   volver a entrar y comprobar la persistencia; validar aislamiento con
   otro estudiante.
5. Adjuntar un PDF pequeño de prueba válido. Verificar que se guarde
   en `.private-media/<id>/pdfs` y no se pueda abrir desde `/media/`.
   **No asumir que el modelo leyó su contenido**: comprobarlo únicamente
   tras desarrollar la funcionalidad explícita de análisis de PDF.
6. Enviar un audio WAV/MP3 de prueba y verificar su transcripción usando
   el motor de audio instalado. El tratamiento automático como pregunta
   es una mejora pendiente, no un comportamiento garantizado.
7. Deshabilitar Ollama, simular un fallo de disco y comprobar errores
   controlados, sin salida de información privada en logs.

## 2. Cuestionarios, simulacros, explicaciones e historial

`Principal.test_cierre_integral` cubre el banco inglés:
generación → claves solo servidor → respuestas → 100 % esperado →
persistencia de respuestas y explicación → no recalificación →
historial solo del alumno. Para la modalidad de 50 preguntas comprueba
las cinco áreas, la calificación y que no se reenvíe el intento.
El generador de preguntas de otras materias depende de Ollama:
revisar en navegador que las preguntas sean correctas y apropiadas,
las opciones plausibles y las explicaciones pedagógicas válidas.

## 3. Roles y acceso cruzado

Ya están disponibles `Principal.test_matriz_permisos_roles`,
`Principal.test_seguridad_privacidad` y `Principal.test_portal_academico`.
Cubren administrador, docente, acudiente, estudiante, visitante, permisos
docentes por curso/año y vínculos acudiente-estudiante. La suite integrada
añade navegación entre roles y exportación aislada.
**Pendiente para despliegue multiinstitución:** aislamiento formal
por centro educativo/colegio, no cubierto por el modelo actual.

## 4. Modelo predictivo con datos reales

Comando seguro y de **solo lectura**:

```powershell
python manage.py auditar_cierre
python manage.py entrenar_prediccion
```

Permite ver el número de alumnos/evaluaciones/respuestas y las métricas
de suficiencia (elegibilidad y clases), sin exportar sus registros.
No publica ni entrena un modelo. El archivo del modelo es privado.

**No ejecutar `--entrenar` hasta verificar consentimiento, calidad
de datos y metodología.** La publicación es condicional a validación
fuera de muestra. GitHub no dispone de la base de alumnos y por ello
no puede confirmar suficiencia o desempeño real.

## 5. Privacidad, eliminación, seguridad y protección de main

- La exportación tiene `no-store` y se limita al usuario autenticado.
- No incluye ChromaDB, LangGraph, adjuntos, backups ni medios heredados.
- El borrado administrativo programa limpieza de carpetas privadas
  al confirmar la transacción; copias y medios antiguos tienen otro
  ciclo de vida. No prometer eliminación irreversible.
- Para despliegue real usar variables de entorno, TLS y backups cifrados
  fuera del repositorio. Probar recuperación de respaldos y retención.
- **Protección de main:** es una configuración de GitHub fuera del código.
  En `Settings → Rules → Rulesets`, para `main` exigir PR, bloquear
  push forzado y borrado, exigir 5 checks (Ruff/Black, ESLint, Stylelint,
  Django y Playwright). Confirmar la regla activa en GitHub.
  La aplicación conectada no tiene permiso de administración para
  activarla; un PR fusionado NO significa que main esté protegida.

## Ejecución reproducible

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_cierre_integral Principal.test_matriz_permisos_roles Principal.test_seguridad_privacidad Principal.test_prediccion_academica
python manage.py test Principal
python manage.py auditar_cierre
# Solo si el modelo Ollama y servidor local están disponibles:
python manage.py auditar_cierre --ollama
```

Las comprobaciones de GitHub no usan ni modifican el SQLite del operador.
Antes de declarar el proyecto listo para producción institucional, completar
las pruebas manuales con audio/IA/memoria reales y revisión pedagógica.
