# Fase 3 — Normalización de HTML y componentes reutilizables

Se reorganizaron las plantillas conservando la lógica Python, las URLs, los
formularios POST, CSRF, permisos, nombres de campos y las clases CSS utilizadas
por las fases 1 y 2. **Sin migraciones ni cambios en los datos.**

## Componentes incorporados

| Componente | Uso real |
| --- | --- |
| `components/alert.html` | Mensajes de error/éxito de Docentes, Permisos, Orientación, Plan semanal y Actividades |
| `components/info_card.html` | Tarjetas informativas de Privacidad y Predicción sin modelo |
| `components/metric_card.html` | Indicadores superiores de Gestión de usuarios |
| `components/metric_item.html` | Métricas de evaluación predictiva |
| `components/form_field.html` | Los 12 campos del Registro; mantiene widgets y errores originales |
| `components/table.html` | Tablas responsivas de usuarios y personas, con encabezados y filas en parciales |
| `components/tables/*.html` | Encabezados y filas de las dos tablas administrativas |
| `components/form_modal.html` | Seis modales Bootstrap de altas en gestión académica y de estudiantes/acudientes |

Estos componentes usan **`{% include %}` nativo de Django**. No se crea un
motor de componentes paralelo, no se añade JavaScript innecesario y el HTML
dinámico se escapa de manera habitual en Django. Los atributos de iconos y
clases se suministran desde literales internos, no desde valores del usuario.

Las tablas conservan los identificadores `users-table`, `user-search`,
`role-filter` y `table-count`; `admin-users.js` sigue aplicando los filtros.
Los modales mantienen `name="form"` / `value` esperados por Django, el
token CSRF y los atributos Bootstrap `data-bs-dismiss` / `id` de apertura.
Ningún botón de eliminación cambia de método POST.

## Revisión de plantillas heredadas

Comparación de `Principal/urls.py`, `Principal/views.py`,
`Principal/management_views.py`, `Principal/portal_academico.py`,
`Principal/historial_views.py` y `Principal/simulacros_views.py`:

- **En uso y conservadas:** `PerfilDeUsuario.html` aparece en
  `views.py`; `acudiente.html` aparece en `management_views.py`;
  `home_admin.html` se usa como plantilla base de gestión de catálogos;
  `PanelDocente.html` y `PanelAcudiente.html` están conectadas por
  `portal_academico.py`; las plantillas de administración de datos siguen
  siendo necesarias.
- **Candidatas a revisión futura:** `Carreras.html`,
  `cordinador.html`, `docentes.html` y
  `editarPerfilDeUsuario.html` no aparecen como destinos literales
  de renderizado en los controladores revisados. La ruta
  `docentes/` está comentada actualmente. **Esto no prueba ausencia de
  referencias dinámicas, pruebas antiguas o usos externos.**
- **Decisión:** no borrar ninguna plantilla antigua en esta fase; primero
  será necesario revisar rutas, enlaces, plantillas heredadas, documentación
  y uso real en el navegador para retirar código con garantías.

## Pruebas y seguridad

El archivo `Principal/test_componentes_html.py` comprueba componentes
escapando contenido potencialmente peligroso, asociación de etiquetas y
widgets de Django, tablas administrativas, campos y formularios POST,
modales Bootstrap con CSRF, URLs y compilación de plantillas actualizadas.
También verifica la ausencia de `onclick`, `onsubmit`, `onchange`,
`oninput` y `onload` escritos como atributos en esas plantillas.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test Principal.test_componentes_html -v 2
python manage.py test Principal
node --test tests/javascript/*.test.cjs
python -m unittest discover -s tests/styles -p "test_*.py" -v
```

GitHub Actions ejecuta Django, JavaScript y CSS antes de fusionar.
Las pruebas automatizadas no sustituyen una inspección visual en varios
tamaños de pantalla ni la comprobación manual de formularios con datos reales.

## Reglas para próximas pantallas

1. Reutilizar tarjetas y alertas antes de copiar HTML.
2. Mantener las etiquetas `label for` asociadas al identificador real.
3. Las tablas deben tener encabezados y títulos accesibles; no inventar
   HTML a partir de cadenas con `safe`.
4. Los formularios deben preservar CSRF, `name`, `value`, URL y método.
5. No usar eventos JavaScript inline ni borrar plantillas heredadas sin
   revisión de referencias.
