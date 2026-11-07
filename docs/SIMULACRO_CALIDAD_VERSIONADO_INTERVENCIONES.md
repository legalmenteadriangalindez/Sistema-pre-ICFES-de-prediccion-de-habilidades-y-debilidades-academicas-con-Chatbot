# Cierre de prioridades muy altas — Pre-ICFES (noviembre 2026)

## 1. Simulacro avanzado recuperable

Ruta del estudiante: `/simulacros/avanzado/`. **Es práctica original, no el
examen oficial Saber 11 ni una predicción del puntaje ICFES.**

- Crea 50 preguntas originales con cinco áreas, en dos bloques de 25.
- Cada bloque tiene 75 minutos de práctica configurados del lado servidor,
  no equivalentes a los tiempos oficiales.
- Los datos de sesión, preguntas originales, claves y respuestas se conservan
  en `SimulacroAvanzado` en la **base de datos**, no en el almacenamiento
  del navegador. La URL no transmite ni expone claves.
- Guarda la alternativa al seleccionarla mediante POST protegido con CSRF.
  Comprueba que el bloque y la alternativa pertenecen al examen actual.
- Permite pausar, salir, iniciar sesión de nuevo y continuar con el tiempo
  restante. La pausa congela el tiempo de la práctica (a diferencia del examen
  oficial). Un bloque con tiempo agotado no puede reanudarse.
- Impide volver a un bloque cerrado, califica una vez y crea un solo
  `IntentoEvaluacion` con sus 50 `RespuestaEvaluacion`.
- Resultados y explicaciones accesibles exclusivamente al dueño del examen.
- Los simulacros anteriores en `/simulacros/` se conservaron sin alterar.
- La guía ICFES 2026 puede consultarse aquí:
  https://www.icfes.gov.co/evaluaciones-icfes/saber-11/guia-de-orientacion-examen-saber-11/
  Su estructura y puntajes **no se reproducen** con un banco actual de 50 ítems.
  Una equivalencia oficial exigiría banco validado y diseño específico,
  incluyendo formas y tiempos. No se recolecta cuestionario socioeconómico.

## 2. Calidad estadística de preguntas

Ruta restringida a docentes autorizados y administración:
`/banco-preguntas/calidad/`.

- Índice de facilidad: **aciertos / estudiantes distintos**; se usa solo
  la respuesta más reciente de cada estudiante para reducir duplicados.
- Señala preguntas con menos de 20 estudiantes como insuficientes; solo
  con un tamaño adecuado marca como muy fáciles (p≥0,9) o muy difíciles
  (p≤0,2).
- Discriminación por grupos extremos: diferencia de proporción de aciertos
  entre el 27 % de mejor desempeño y el 27 % de menor desempeño, ordenados
  por el puntaje **sin la pregunta evaluada**. Se muestra con 20 o más
  estudiantes con intentos de al menos 4 preguntas.
- Alfa de Cronbach exploratorio solamente si al menos 30 estudiantes
  distintos respondieron exactamente el mismo conjunto de 3 o más ítems.
  Si la varianza total es 0, no se informa alfa.
- Todo el reporte es agregado; no expone nombres de menores. Los valores
  no certifican validez, equivalencia ni discriminación oficial ICFES.

## 3. Versionado inmutable de preguntas

- Desde el banco, el autor o administrador propone **Nueva versión** de
  una pregunta vigente aprobada.
- Se crea un **borrador con nuevo ID** (`numero_version` creciente),
  manteniendo la fila original inalterada. Se permite conservar el
  mismo enunciado y corregir opciones/clave/explicación.
- El borrador vuelve a pasar por otro revisor autorizado; está prohibida
  la autoaprobación.
- Tras la aprobación, la versión nueva se activa para prácticas futuras;
  las anteriores se archivan (no se borran).
- Las respuestas antiguas conservan `pregunta_banco_id` original y
  sus textos, claves y explicaciones tal como fueron respondidos.
- La vista de historial incluye autor, revisor, estado, fecha y versiones.
  Solo el equipo de curaduría ve las respuestas correctas.

## 4. Intervenciones académicas docentes

- Docente: `/panel-docente/intervenciones/`
- Estudiante: `/intervenciones/mias/`
- Crear un plan por estudiante autorizado, materia, competencia, objetivo,
  acciones y fecha de seguimiento.
- El resultado inicial se calcula al crear el plan a partir de respuestas
  históricas comparables; la medición posterior se congela al cerrar.
  Se exige al menos **dos respuestas** en cada momento para mostrar
  porcentajes. Sin evidencias se indica explícitamente «no calculable».
- Solo el docente creador de la intervención, con curso/año aún autorizado,
  puede cerrarla; los estudiantes ven únicamente sus propios planes.
- Una mejora descriptiva **no demuestra causalidad**: factores de tiempo,
  dificultad de examen, efecto práctica y otros deben estudiarse aparte.

## Despliegue seguro en local

Antes de migrar: respaldar PostgreSQL o SQLite y comprobar que el respaldo
pueda restaurarse. La migración `0017` es aditiva y no borra respuestas.

```powershell
git pull origin main
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test Principal.test_prioridades_muy_altas
python manage.py test Principal
python manage.py runserver
```

Tests browser: `npm run test:browser` (CI usa cuentas sintéticas).

## Limitaciones antes de un despliegue institucional

- El simulacro avanzado actual no usa un banco oficial ni reproduce la
  duración/puntaje del ICFES; el historial no contiene equivalencia IRT.
- La pausa detiene el tiempo únicamente de la **práctica virtual**.
- Revisar en navegador real el comportamiento con interrupciones
  de red, múltiples pestañas y varios dispositivos.
- La base real puede no tener suficientes respuestas para métricas
  psicométricas; no completar con valores sintéticos ni ocultar faltantes.
- No se activa automáticamente protección de `main`: requiere Rulesets
  con permisos administrativos en GitHub.
- Los cuatro módulos dependen de migración y variables de entorno de la
  instalación real; fusionar a GitHub `main` **no equivale** a desplegar
  automáticamente una instancia de servidor externa.
