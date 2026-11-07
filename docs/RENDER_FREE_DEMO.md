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
- Portada pública original en `/`, sin acceder a datos personales.
- El registro de usuarios reales, interfaces administrativas, carga de
  archivos y cambios de identidad quedan bloqueados mediante middleware.
- El tutor IA (PDF/audio, memoria) queda deshabilitado al no existir un
  motor Ollama ni almacenamiento persistente de conversaciones.
- El comando `crear_usuarios_prueba` crea cuentas **ficticias**, sin
  superusuario, con contraseña aleatoria guardada exclusivamente en
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
   `/readyz/` y la portada `/`.
6. Para iniciar sesión con cuentas sintéticas (`estudiante_ana`,
   `estudiante_luis`, `docente_demo`), consultar
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
