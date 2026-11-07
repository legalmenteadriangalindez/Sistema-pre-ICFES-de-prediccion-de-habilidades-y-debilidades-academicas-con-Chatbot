# Pre-ICFES en Render gratuito — demostración temporal

> **Nunca utilizar con datos personales reales, estudiantes menores, historiales
> auténticos ni documentos privados.** Esta modalidad no equivale a un
> despliegue institucional de producción.

## Infraestructura de coste cero

La plantilla **`render-free.yaml`** (separada de `render.yaml` para producción)
define:
- Un Web Service **Free** de Python con Gunicorn/WhiteNoise y HTTPS de Render.
- Una base **PostgreSQL Free**, 1 GB y **caducidad a los 30 días**.
- **Ningún disco persistente**: el directorio `/tmp/preicfes-free-demo`
  es temporal; ningún PDF, ChromaDB, conversación del tutor ni modelo
  guardado en archivos sobrevivirá a un redeploy, reinicio o suspensión.
- El web se suspende tras 15 minutos sin uso; el siguiente visitante puede
  esperar aproximadamente un minuto durante su reactivación.
- El demo consume el límite de 750 horas gratuitas por workspace, además
  de las cuotas de tráfico y minutos de construcción de Render.
- PostgreSQL Free no ofrece respaldos gestionados; al expirar se hace
  inaccesible y luego se elimina según la política vigente.

Documentación: https://render.com/docs/free

## Protecciones añadidas al demo

- `DJANGO_ENV=demo` usa `DEBUG=False`, clave secreta obligatoria,
  cabeceras HTTPS y cookies seguras, PostgreSQL obligatorio y
  `RENDER_EXTERNAL_HOSTNAME` para ALLOWED_HOSTS/CSRF.
- **Misma interfaz que en local**: la ruta `/` utiliza el inicio y la
  navegación originales de Django; el usuario sin sesión ve el login,
  y al ingresar entra en el tablero correspondiente a su rol.
  La antigua portada promocional se conserva en `/demo/`.
- El tablero del estudiante usa `home.html`, con estadísticas de
  las cuentas ficticias y el componente del tutor visible pero apagado.
- Los cuestionarios de asignaturas utilizan preguntas predefinidas del
  banco local, sin llamadas a Ollama y con calificación real.
- La demo incluye `admin_demo` como **ADMIN de aplicación, sin ser
  superusuario Django**. Puede consultar paneles sintéticos sin
  crear, modificar o eliminar usuarios, matrículas o catálogos.
- El registro de usuarios reales, los cambios administrativos, los
  cambios de credenciales y la carga de archivos quedan bloqueados;
  los paneles administrativos siguen disponibles en modo lectura.
- El tutor IA (PDF/audio, memoria) queda deshabilitado al no existir un
  motor Ollama ni almacenamiento persistente de conversaciones.
- El comando `crear_usuarios_prueba` crea cuentas **ficticias**, incluido un ADMIN de solo lectura,
  pero sin superusuario, con contraseña aleatoria guardada exclusivamente en
  `PREICFES_DEMO_PASSWORD` de Render y jamás mostrada en logs.
- Las evaluaciones pueden usarse con esos usuarios ficticios para
  explorar parte de la plataforma. Las cuentas de demo pueden compartir
  datos simulados y no deben usarse para consultas privadas.
- La configuración de producción `render.yaml` no se modifica.

## Despliegue

1. Sincronizar la rama `main` con GitHub Actions completo en verde.
2. En Render, abrir el Blueprint correspondiente a `render-free.yaml`.
3. **Revisar el plan**: debe listar exactamente un web `plan: free`
   y una DB `plan: free`, sin disco, con cero recursos de pago.
4. Aprobar el plan explícitamente desde Render, y no activar upgrades.
5. En Render, abrir el servicio y verificar `/healthz/`,
   `/readyz/`, la redirección de `/` a `/accounts/login/` y los
   tableros de estudiante, docente, acudiente y administrador.
6. Para iniciar sesión con cuentas sintéticas (`estudiante_ana`,
   `estudiante_luis`, `docente_demo`, `acudiente_demo`, `admin_demo`), consultar
   `PREICFES_DEMO_PASSWORD` en Environment del propio servicio
   (nunca publicarla). El comando de siembra no imprime secretos.
7. No publicar ni inscribir estudiantes reales. Sustituir este servicio
   por una infraestructura persistente y auditada antes de un piloto.

Si Render devuelve `need_payment_info` incluso para un plan 100 %
gratuito, informar de ello y **no aceptar automáticamente planes
alternativos pagados**.

## Mantenimiento

Las contraseñas sintéticas se conservan entre reinicios mientras exista
PostgreSQL. La base Free expira a los 30 días. La cuenta podrá tener que
crear otra base de demostración y volver a sembrar datos ficticios.
Las estadísticas del demo no constituyen evidencia psicométrica de calidad.

## Diferencias deliberadas respecto al servidor local

La estructura visual, navegación y páginas académicas son las mismas.
No se ejecuta el chatbot, su memoria, audio ni PDF; los controles de chat
están ocultos o inactivos y el tablero indica esa limitación. Los
cuestionarios sin IA usan el banco estático original. La administración
solo permite lectura y no se admiten registros reales ni edición de
credenciales. Son restricciones de seguridad para compartir la URL.
