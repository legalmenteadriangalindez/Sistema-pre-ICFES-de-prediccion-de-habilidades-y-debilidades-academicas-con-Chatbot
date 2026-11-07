# Banco de preguntas revisadas y práctica adaptativa — Pre-ICFES

## Flujo operativo

1. Un docente con matrícula autorizada o un administrador accede a
   **Banco de preguntas** desde su panel.
2. Crea una pregunta con materia, competencia, evidencia pedagógica opcional, dificultad, contexto opcional,
   cuatro alternativas A–D, una clave y explicación; o solicita al generador
   local Ollama un **borrador de IA**.
3. Puede corregir un borrador propio y enviarlo a revisión. No puede
   aprobarlo ni editarlo mientras esté en revisión o aprobado.
4. **Otra persona autorizada**, docente o administrador, revisa y aprueba
   o rechaza con observaciones. El rechazo requiere al menos 10 caracteres
   y devuelve la pregunta a su autor para corrección.
5. Solamente `APROBADA` y `activo=True` entra en la práctica adaptativa.
   Los formularios muestran la clave exclusivamente a los revisores
   autorizados. No se publica automáticamente contenido sugerido por IA.
6. El estudiante entra en **Práctica adaptativa**, recibe hasta 5 preguntas,
   responde en un máximo de 30 minutos y obtiene calificación y explicación
   al finalizar. El resultado queda registrado en su historial mediante
   `IntentoEvaluacion` y `RespuestaEvaluacion`.

## Seguridad y metodología

- La comparación de preguntas duplicadas utiliza SHA-256 sobre materia y
  enunciado normalizados; se protege con unicidad en la base de datos.
- La práctica utiliza sesión **servidor/DB** de Django, asociada a usuario
  y estudiante. La clave de respuesta y el identificador del banco no
  aparecen en el formulario antes de enviar.
- Una segunda calificación es rechazada; una nueva práctica no reutiliza
  el intento anterior. Las preguntas utilizadas pueden repetirse solo
  después de agotar las alternativas disponibles.
- Selección adaptativa **basada en reglas**: de las últimas 300 respuestas
  del estudiante se identifican competencias con al menos 2 evidencias y
  menos de 60 % de aciertos. Se priorizan preguntas de esas competencias y
  luego áreas con desempeño bajo; sin evidencia suficiente se ofrecen
  materias variadas. Es una guía de refuerzo, **no un modelo de IA entrenado,
  una estimación causal ni el puntaje oficial ICFES**.
- Los resultados de esta práctica alimentan `seguimiento.py` y el
  diagnóstico/plan semanal futuro. No se utilizan para entrenar el modelo
  predictivo que exige otros tipos de eventos.
- La revisión es obligatoria para todos los borradores, incluso los
  generados por el LLM. La responsabilidad pedagógica y el respeto por
  derechos de autor pertenecen al revisor de la institución.
- El banco nuevo comienza vacío: los bancos estáticos existentes de
  inglés/simulacros **no se publican automáticamente** y no cambian.
  Los cuestionarios tradicionales y los simulacros siguen operando igual.
- Los intentos anteriores no se alteran: `pregunta_banco` en cada
  respuesta es una FK opcional con `SET_NULL` para proteger el historial.
- Esta versión evita edición de preguntas ya publicadas; cualquier
  corrección de una pregunta aprobada deberá realizarse mediante un
  futuro proceso de versionado y nueva aprobación, para no alterar su
  contexto histórico.

## Instalar en entorno local

Respaldar primero la base de datos. En una consola con entorno virtual:

```powershell
git pull origin main
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_banco_preguntas_adaptativo
python manage.py test Principal
python manage.py runserver
```

Para probar borradores IA, iniciar Ollama y verificar el modelo instalado
mediante `ollama list`. No es necesario tener Ollama activo para crear,
revisar, aprobar o resolver preguntas manuales.

Pruebas E2E Chromium: `npm run test:browser`. El test de banco crea
cuentas y datos sintéticos únicamente en la base efímera de CI. No se
suben registros de menores ni de instituciones al repositorio.

## Limitaciones conocidas

La selección se restringe a 500 preguntas publicadas; no hay todavía
paginación de catálogo, versionado de preguntas aprobadas ni revisión
de plagio semántico. La huella identifica duplicados literales
normalizados, no paráfrasis. La supervisión profesional sigue siendo
esencial antes de usar contenidos en un entorno institucional.

La protección de `main` se configura en GitHub Settings → Rulesets,
no dentro del código Django.
