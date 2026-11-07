# Segunda etapa: funciones educativas, datos y seguridad

## Funcionalidades incorporadas

- Repetición espaciada: solo preguntas curadas aprobadas; intervalos de
  1, 3, 7, 14, 30 y 60 días, con prioridad para repasos vencidos. La
  programación se actualiza en la misma transacción que la calificación.
- Progreso longitudinal: compara las primeras tres y últimas tres
  respuestas de la misma competencia, si existen seis o más evidencias.
  No implica mejora causal ni predicción de puntajes ICFES.
- Tutor con fuentes: búsqueda textual limitada a contenido aprobado,
  con identificadores B-id y fichas de lectura; no busca durante un
  simulacro activo. Sigue requiriendo Ollama para respuestas generativas.
- Importación académica: CSV UTF-8 o XLSX de hasta 2 MB/500 filas con
  columnas documento,curso_id,anio. Solo importa matrículas de usuarios
  existentes, valida cupos, previene duplicados y rechaza el lote
  completo cuando detecta inconsistencias.
- Exportación: CSV compatible con Excel, autorizado para docentes de
  los cursos asignados o administradores; las celdas de texto se
  protegen contra fórmulas peligrosas.
- Auditoría/privacidad: rastrea operaciones sensibles con metadatos
  mínimos, amplía el JSON de exportación propia, registra autorización
  y revocación del tutor IA por un acudiente formalmente vinculado.
  La IA para menores requiere esa autorización.
- Notificaciones: bandeja de avisos internos de retroalimentación y
  planes de intervención, sin correos o SMS externos, con control de
  preferencias y marcado de lectura.
- Accesibilidad: controles de contraste y tamaño de letra, foco visible,
  reducción de movimiento y recuperación de estado visual. En el
  simulacro, un error de guardado bloquea la finalización hasta
  solucionar la conexión.

## Rutas

- Estudiantes: /repasos/, /progreso-competencias/, /avisos/
- Docentes: /progreso-competencias/?matricula=ID y
  /gestion/reportes/exportar/
- Administradores: /gestion/matriculas/importar/
- Acudientes: /privacidad/consentimiento-ia/
- Tutor: /material-validado/ID/ tras referencia de contenido aprobado

## Datos de menores y límites

El consentimiento del acudiente vinculado se comprueba en servidor.
Esto no constituye por sí mismo un programa integral de protección de
datos personales: siguen pendientes revisión de políticas, bases
legales, derechos ARCO, almacenamiento externo ChromaDB/LangGraph,
copias de seguridad, contratos y evaluación de riesgos institucional.

Para revisar retención:

```powershell
python manage.py retencion_datos_educativos
```

Para aplicar borrado **solo de metadatos vencidos** (por defecto
365 días de auditoría, 180 días de avisos):

```powershell
python manage.py retencion_datos_educativos --aplicar
```

No se eliminan intentos, estudiantes ni calificaciones.

## Multiinstitución: pendiente de aislamiento completo

Esta entrega NO habilita un modo multiinstitución seguro. El modelo
actual de cursos y catálogos necesita una migración de claves y
aislamiento por institución en **todas** las vistas, relaciones,
consultas, archivos y tareas; añadir un campo a Curso sin
auditar todo el sistema generaría fugas entre colegios.
Se conserva el acceso por curso/año y la administración global
existente. El soporte multiinstitución debe desarrollarse y
validarse por separado antes de alojar información de varios colegios.

## Activación

Respaldar PostgreSQL/SQLite, actualizar código y aplicar la migración
0018 antes de usar las pantallas nuevas:

```powershell
git pull origin main
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test Principal.test_funciones_pendientes
python manage.py test Principal
python manage.py runserver
```

La base académica anterior se conserva. Para XLSX se agregó
openpyxl a requirements.txt, instalado con:
`pip install -r requirements.txt`.

GitHub main != publicación automática a un servidor; confirmar la
configuración de despliegue, la migración en producción y Rulesets.
