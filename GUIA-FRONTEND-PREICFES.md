# Pre-ICFES — actualización visual y funcional (2026)

Esta actualización **no elimina modelos, migraciones ni historiales**. Conserva el frontend
actual (`ui-2026.css` y `ui-2026.js`), y agrega una capa de presentación más refinada:

- Chat con burbujas legibles, estados vacíos centrados, preguntas rápidas y compositor flexible.
- Simulacros con progreso, reloj, opciones seleccionables, navegador y resumen en pantalla.
- Gestión de usuarios con cifras reales, tabla, búsqueda, filtro y acciones con permisos.
- Configuración local: modo oscuro, escala tipográfica, reducción de movimiento y acceso seguro a perfil/contraseña.
- Estilos coherentes para recomendaciones, perfil, actividades e historial.
- Diseño adaptable a pantallas pequeñas y estados de foco accesibles.

Las cifras mostradas **proceden de la base**; los mockups son ilustrativos.

## Aplicar desde GitHub

Detén el servidor Django, respalda tu proyecto (especialmente `.env`, `local.sqlite3`,
`Principal/migrations/0012*` y `media/`), y desde tu clon Git ejecuta:

```powershell
git status
git pull origin main
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py test Principal.test_ui_premium Principal.test_ui_polish
python manage.py runserver
```

Si `git status` muestra modificaciones locales, no hagas `git reset --hard` ni
sobrescribas tu migración corregida: respalda antes los cambios o aplícalos manualmente.
No es necesario borrar la base, regenerar usuarios ni ejecutar `makemigrations` para
los cambios visuales de esta actualización.

Ollama es independiente de Django. Las respuestas del tutor requieren que su servicio
esté activo y que el modelo configurado en `.env` esté descargado.

## Pruebas

Las pruebas de frontend verifican acceso y controles de rol sin usar Ollama. Los
exámenes siguen comprobándose y calificándose en el servidor. Antes de desplegar,
verifica el flujo completo en Windows con cuentas de estudiante y administrador.
