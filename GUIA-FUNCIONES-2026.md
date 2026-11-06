# Funciones académicas incorporadas

## Incluidas

- **Orientación vocacional exploratoria** (`/orientacion-vocacional/`): 12 afirmaciones, respuestas de 1 a 5, cuatro dimensiones y cinco carreras sugeridas. En estudiantes con matrícula activa guarda recomendaciones usando la tabla existente `RecomendacionVocacional`. Al repetir, sustituye solamente recomendaciones creadas por este cuestionario. Los valores 0–100 son afinidades orientativas, no probabilidades ni pruebas psicométricas.
- **Comparador** (`/compararCarreras/`): selecciona hasta tres carreras y muestra descripciones y afinidad registrada, cuando existe. No inventa costos, salarios, requisitos ni duración.
- **Diagnóstico académico descriptivo** (`/diagnostico-academico/`): calcula resultados por materia y dificultades por competencia a partir de `RespuestaEvaluacion`. No es un sistema de predicción de aprendizaje automático. Los umbrales se presentan como criterios de apoyo, no probabilidades.
- **Plan semanal sugerido** (`/plan-semanal/`): siete actividades propuestas basadas en áreas medidas. Si no hay evaluaciones, muestra una rotación general. No sustituye asignaciones formales ni crea registros de agenda; es una guía regenerable.
- **Docentes** (`/panel-docente/`): permite crear actividades con tema y nivel existentes, asignarlas a una matrícula activa, impedir duplicados y visualizar las asignaciones recientes. Sólo se habilita para el rol `DOCENTE` o superusuario.
- **Acudientes** (`/acudiente/`): muestra exclusivamente estudiantes con vínculo `EstudianteAcudiente` asociado a la cuenta, sus últimas evaluaciones y número de tareas pendientes.
- **Simulacro integral ampliado**: nuevo formato opcional de 50 preguntas originales (10 por área, incluyendo inglés). El formato básico permanece sin cambios, para conservar compatibilidad y pruebas previas.
- **Navegación según rol**: `DOCENTE` y `ACUDIENTE` llegan a sus respectivos paneles al iniciar; los administradores mantienen su panel y los estudiantes su inicio habitual.

## Consideraciones técnicas

- Sin migraciones nuevas: se reutilizan las tablas actuales. Mantén y respalda las migraciones 0001–0012.
- El proyecto sigue necesitando Ollama y el modelo configurado para tutor IA y generación LLM de cuestionarios. Las nuevas rutas no dependen de Ollama.
- El esquema no tiene una relación Docente–Curso o Colegio–Usuario. El panel docente está destinado **únicamente a una instalación de una sola institución**. No es adecuado para despliegues multiinstitución sin permisos adicionales.
- No se implementó un predictor ML validado. La clasificación de áreas por reforzar usa estadísticas descriptivas y debe etiquetarse como tal.
- El conjunto de preguntas es de práctica, **no es un simulacro oficial del ICFES** ni reproduce un examen completo oficial.

## Pruebas

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_portal_academico Principal.tests Principal.test_ui_premium Principal.test_ui_polish
python manage.py runserver
```

Si tu base SQLite ya aplicó `0012`, no la elimines ni vuelvas a generar migraciones. Primero respalda cualquier dato importante antes de actualizar código.
