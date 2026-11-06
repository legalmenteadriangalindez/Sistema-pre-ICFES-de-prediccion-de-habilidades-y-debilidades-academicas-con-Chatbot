# Fase 4 — Vistas Django por dominio y fachadas de compatibilidad

## Objetivo

La lógica que antes estaba mezclada en `Principal/views.py`,
`Principal/portal_academico.py` y `Principal/management_views.py` se
organizó en `Principal/view_modules/`. Se conservaron las URLs, nombres
de funciones, respuestas JSON/HTML, permisos y decoradores originales.
**No cambia ningún modelo, migración, tabla ni dato de SQLite.**

## Mapa de responsabilidades

| Módulo | Responsabilidad |
| --- | --- |
| `autenticacion.py` | Salir, inicio de sesión, registro, verificación de correo |
| `chatbot.py` | Portada del estudiante, mensajes del tutor, PDF y audio |
| `cuestionarios.py` | Selección, generación y calificación de cuestionarios |
| `perfiles.py` | Consulta/edición de perfil y preferencias |
| `estudiantes.py` | Recomendaciones observadas y actividades asignadas |
| `vocacional.py` | Cuestionario de orientación, comparador y vista anterior |
| `seguimiento.py` | Diagnóstico y plan semanal persistente |
| `docentes.py` | Autorización por pareja (curso, año) y panel docente |
| `acudientes.py` | Seguimiento familiar y vista heredada |
| `admin_docentes.py` | Asignaciones y revocaciones de permisos docentes |
| `admin_usuarios.py` | Cuentas, personas, roles y borrado privado |
| `admin_catalogos.py` | Catálogos de grado, curso, materias, años, roles y sexo |
| `admin_matriculas.py` | Gestión administrativa de estudiantes y acudientes |
| `selectores.py` | Ayudas comunes de autorización, estudiante y matrícula |

Las fachadas `views.py`, `portal_academico.py` y
`management_views.py` ahora importan y reexportan nombres.
`Principal/urls.py` y todos los nombres `reverse(...)` se
mantienen **exactamente iguales**.

## Compatibilidad con pruebas existentes

Algunas pruebas usan patch en la fachada original:
- `Principal.views.chatbotManager.get_chatbot` para aislar Ollama.
- `Principal.views.render` para observar la portada del estudiante.
- `Principal.views.generar_quizes` y `generar_material` para cuestionarios.
- `Principal.views.enviar_verificacion` para el correo.
- `Principal.portal_academico.timezone.localdate` para congelar el reloj.

Se conservaron estos símbolos; la fachada delega los argumentos
sustituibles al módulo específico. El alias `timezone` continúa
apuntando al mismo módulo `django.utils.timezone` que usa Seguimiento.

### Reglas para nuevos cambios

- Agregar funcionalidades a su archivo de dominio, **no** a la fachada.
- Nunca importar `Principal.views` o `management_views` desde un
  `view_modules/*.py`: eso crearía importaciones circulares.
- Los chequeos por rol compartidos viven en `selectores.py`.
- Conservar POST, CSRF y decoradores al mover una vista.
- No modificar el contrato de parámetros ni el contexto de plantillas
  sin pruebas de regresión.
- El chatbot y el módulo de cuestionarios todavía integran servicios
  existentes; su separación interna en unidades más pequeñas pertenece
  a la fase 5 y requiere pruebas de comportamiento adicionales.

## Validación

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_modularizacion_vistas -v 2
python manage.py test Principal
node --test tests/javascript/*.test.cjs
python -m unittest discover -s tests/styles -p "test_*.py" -v
```

La batería nueva comprueba que `reverse` conserva callbacks, que
usuarios anónimos no acceden a las vistas protegidas, que las rutas
administrativas de eliminación siguen protegidas y que no hay ciclos
de importación entre módulos nuevos y fachadas. Todas las regresiones
anteriores de Django siguen siendo obligatorias antes de fusionar en
`main`.

El navegador real, la conectividad con Brevo y Ollama y la base de
datos de producción no están incluidos en GitHub Actions. Es necesario
comprobarlos en un entorno autorizado antes de desplegar.
