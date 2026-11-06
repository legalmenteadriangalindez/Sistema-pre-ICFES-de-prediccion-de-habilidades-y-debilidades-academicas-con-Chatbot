# Predicción académica responsable: metodología y límites

## Estado del módulo

El código implementa extracción de datos, entrenamiento, evaluación de
desempeño, controles de publicación y alertas individuales. **No incorpora
datos privados, un modelo entrenado ni métricas obtenidas de alumnos reales
al repositorio.** Para comprobar si los datos disponibles alcanzan, ejecutar
`python manage.py entrenar_prediccion` sobre una base de datos autorizada.

No se debe rellenar un dataset insuficiente con ejemplos inventados para
publicar un modelo como si hubiera sido evaluado con estudiantes reales.
Las muestras sintéticas aparecen exclusivamente dentro de tests automatizados.

## Pregunta y etiqueta

**Pregunta:** ¿el siguiente intento de una *misma materia* tendrá un
porcentaje de respuestas correctas inferior al 60 %?

- Etiqueta positiva `riesgo=1`: próximo intento del área con aciertos /
  preguntas inferior a 0,60.
- Etiqueta negativa `riesgo=0`: próximo intento con al menos 0,60.
- Unidad de análisis: un intento *por materia*. En un simulacro integral,
  las respuestas se separan por una de las cinco áreas Saber 11.
- Solo se incluyen eventos con al menos **5 preguntas válidamente
  calificadas** en la materia.
- Antes de cada etiqueta se exigen **dos o más intentos anteriores** de la
  misma materia del mismo estudiante.
- El 60 % es un **umbral operativo exploratorio**, no una regla ICFES
  oficial ni un diagnóstico de habilidades.
- El modelo **no** predice el puntaje global Saber 11 ni el éxito académico
  futuro del estudiante.

## Datos de entrada y minimización

Se consultan `IntentoEvaluacion` y `RespuestaEvaluacion`. Las variables
de entrada tienen únicamente información histórica: último porcentaje,
promedio acumulado, cambio entre dos intentos, variabilidad de hasta tres
intentos, cantidad de intentos, preguntas del último intento, intervalo entre
los dos últimos y área académica codificada.

**No** se utilizan documento de identidad, correo, fecha de nacimiento,
sexo, dirección, teléfono, colegio ni texto literal de las respuestas.
El alumno se identifica solo temporalmente para separación de grupos:
el identificador no es una característica del predictor ni se guarda en el
artefacto final.

Se excluyen las cuentas de demostración conocidas de `crear_usuarios_prueba`.
Los centros que utilicen otros usuarios ficticios deben depurarlos antes de
auditar/entrenar.

## Condiciones mínimas para intentar el entrenamiento

| Condición | Mínimo |
| --- | ---: |
| Estudiantes distintos con secuencias etiquetables | 40 |
| Ejemplos temporales (historial previo → intento siguiente) | 150 |
| Ejemplos con resultado inferior al 60 % | 30 |
| Ejemplos con resultado igual o superior al 60 % | 30 |
| Preguntas por evento | 5 |
| Evaluaciones anteriores de la misma área | 2 |

Estos números son **mínimos técnicos iniciales, no una demostración de
suficiencia estadística**. Antes de publicar se comprueba además la
composición real del conjunto de entrenamiento y prueba.

## Entrenamiento, fuga de información y comparación

1. Ordenar intentos de cada alumno y área por fecha y ID.
2. Formar ejemplos con información anterior al intento objetivo (sin
   utilizar el resultado futuro dentro de las características).
3. Separar **25 % de estudiantes completos** para prueba independiente
   (`GroupShuffleSplit`, semilla 42). Ningún estudiante aparece en ambos
   conjuntos, aunque tenga simulacros integrales de varias materias.
4. Exigir por lo menos 25 estudiantes y 20 registros de cada clase en
   entrenamiento, y ocho estudiantes y seis registros de cada clase en
   prueba.
5. Entrenar estandarización de variables y **regresión logística** solo en
   entrenamiento. Evaluar sobre estudiantes nunca vistos.
6. Comparar con `DummyClassifier(strategy="most_frequent")`.
7. Medir precisión de la clase de riesgo, recuperación (sensibilidad),
   F1, exactitud balanceada, AUC-ROC, error Brier y matriz de confusión.
8. Para publicar: exactitud balanceada al menos **0,05 superior** a la
   referencia y precisión/recuperación del riesgo **al menos 0,55**.
9. Solo autorizar predicciones de áreas con suficiente presencia en ambos
   grupos y con precisión/recuperación de riesgo >= 0,50 y exactitud
   balanceada >= 0,55 en la prueba de esa área. **No extrapolar entre
   materias sin validación.**
10. Tras aprobar las pruebas, reentrenar la configuración fija sobre todos
    los ejemplos históricos disponibles. El artefacto es un JSON de
    coeficientes, escalares y métricas, nunca un objeto pickle.

Este holdout por alumno es útil, pero **no constituye validación
prospectiva ni externa**. Antes de afirmar utilidad clínica, institucional o
educativa se necesitan cohortes posteriores, pruebas entre colegios,
calibración, revisión de subgrupos autorizados y seguimiento de deriva.

## Interpretación de métricas

- **Precisión del riesgo:** entre las alertas, fracción que acertó.
- **Recuperación del riesgo:** entre las dificultades observadas, fracción
  detectada por el modelo.
- **F1 de riesgo:** media armónica de precisión y recuperación.
- **Exactitud balanceada:** media del acierto sobre la clase con/sin
  riesgo; evita que una clase predominante maquille la calidad.
- **AUC-ROC:** capacidad de discriminación entre clases, no porcentaje
  de aciertos.
- **Brier:** error cuadrático de puntuaciones probabilísticas; menor es
  mejor, **pero no demuestra calibración confiable**.
- **Matriz de confusión:** verdaderos negativos (VN), falsos positivos
  (FP), falsos negativos (FN) y verdaderos positivos (VP).

Las métricas se publican solo con datos reales en el servidor autorizado.
El repositorio no puede informar un F1 real sin esa evaluación.

## Ejecución en la instalación local

Con el entorno virtual activo y la base autorizada:

```powershell
python manage.py migrate
python manage.py entrenar_prediccion
python manage.py entrenar_prediccion --entrenar
python manage.py test Principal.test_prediccion_academica
python manage.py test Principal
```

El primer comando de predicción **solo audita** volumen y distribución;
no entrena. El segundo intenta entrenar y detiene la publicación si hay
datos insuficientes, separación degenerada o métricas demasiado bajas.

El modelo validado se guarda exclusivamente en
`.local-data/prediccion/modelo.json` (ignorado por Git). No copiarlo ni
subirlo a repositorios públicos. Caduca para consumo después de 180 días y
requiere reentrenamiento. La predicción se muestra en
`/prediccion-academica/`; el administrador consulta auditoría y métricas
en `/gestion/validacion-prediccion/`.

Si no existe un modelo válido o no hay dos intentos previos de un área,
la vista comunica esa limitación. Ningún usuario puede ejecutar el
entrenamiento por HTTP; solo operadores del servidor con permisos de
administración de la instalación.

## Buenas prácticas con menores de edad

Obtener permisos y bases legales antes de recolectar datos de alumnos,
cumplir las reglas locales de protección de datos personales y minimizar
la información retenida. Las alertas se usan solo para recomendar
**práctica adicional**, nunca para negar cupos, evaluar docentes,
establecer notas oficiales o clasificar la inteligencia de un menor.

La muestra es de conveniencia/autoselección, puesto que solo incluye
alumnos que completaron suficientes evaluaciones en la aplicación.
Ese sesgo limita la generalización a todos los estudiantes del país.
