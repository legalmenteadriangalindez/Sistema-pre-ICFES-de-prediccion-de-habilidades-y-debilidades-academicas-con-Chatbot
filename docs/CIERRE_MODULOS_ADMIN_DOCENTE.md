# Funciones docentes y administrativas — fase de cierre (2026)

## Alcance

Se agregaron operaciones a los paneles existentes, preservando rutas históricas
y evitando reescribir las evaluaciones y modelos anteriores. La migración
`0015_docente_autoria_retroalimentacion` incorpora dos campos **opcionales**
de autoría y la tabla de retroalimentación. Las filas antiguas permanecen
con autor nulo y no se reasignan a un docente por suposición.

## Docentes

- Conservan la autorización estricta por la pareja curso/año lectivo.
- Crean actividades con autor y editan **solo sus propias actividades**.
  No se permite modificar actividades ya completadas por alumnos.
- Asignan desde el catálogo; las nuevas asignaciones registran el docente.
  Pueden retirar únicamente tareas que ellos asignaron y siguen pendientes.
  Las asignaciones antiguas sin autor no se retiran desde ese panel.
- Consultan resultados individuales y el porcentaje agregado de aciertos,
  calculado sobre la suma de preguntas de evaluaciones históricas.
  **El historial no se puede atribuir a un curso/año individual**, ya que la
  tabla de intentos guarda estudiante y fecha, no matrícula.
- Envían retroalimentación escrita (10–1000 caracteres) solo a matrículas
  autorizadas. El alumno la ve en `Mis actividades` al tener una matrícula
  activa; otro estudiante no puede verla.

## Administración

- Edición de usuario (sin editar contraseñas ni permisos superusuario),
  persona y necesidades educativas.
- Registro de persona vinculado a una cuenta real, corrigiendo el formulario
  anterior que no permitía seleccionar un perfil.
- Edición de catálogos de grado, curso, materia, año, rol, sexo y relación.
  Formularios de sexos y relaciones corregidos para enviar el tipo correcto.
- Creación y edición de matrícula con una matrícula por estudiante/año y
  validación del cupo del curso, además de desactivación **sin eliminar**
  calificaciones o tareas históricas.
- Creación, edición y revocación de vínculos estudiante-acudiente.
- Reporte agregado de matrículas, tareas y evaluaciones.
- Se bloquea el borrado de registros referenciados desde los endpoints
  antiguos, evitando efectos en cascada sobre datos académicos.

## Limitaciones y controles antes de producción

- Ejecutar `python manage.py migrate` tras respaldar la base de datos.
  No se modificaron migraciones anteriores.
- Los docentes no pueden editar actividades heredadas de autor desconocido.
  Reasignarlas requiere procedimiento administrativo con auditoría.
- El control de cupos usa transacciones; para uso concurrente intensivo es
  preferible un servidor PostgreSQL con bloqueos efectivos (SQLite no
  ofrece los mismos bloqueos de filas).
- El proyecto todavía no separa varias instituciones/colegios.
- El administrador gestiona catálogos y matrículas, pero no se ha diseñado
  un módulo institucional de boletines oficiales, períodos de calificación
  o auditoría legal avanzada; no confundir el reporte actual con ello.
- La protección técnica de la rama `main` requiere habilitar Rulesets en GitHub.

## Pruebas

```powershell
git pull origin main
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_gestion_completa_roles Principal.test_seguridad_privacidad
python manage.py test Principal
```

Revisar visualmente los paneles con un docente autorizado, otro docente
sin permisos, un estudiante, un acudiente y un superusuario. Las pruebas
automáticas de GitHub utilizan exclusivamente datos sintéticos.
