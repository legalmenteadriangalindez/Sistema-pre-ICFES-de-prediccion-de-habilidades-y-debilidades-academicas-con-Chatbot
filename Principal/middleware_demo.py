"""Permisos de la demo: misma navegación local, sin cambios de cuentas reales.

Las cuatro vistas académicas principales siguen operativas con datos ficticios.
Se permite inspeccionar administración sintética, pero no crear, editar ni borrar
cuentas o catálogos desde un servidor público con contraseñas compartidas.
"""
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseNotFound


class BloqueoDemoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.DEMO_MODE:
            return None

        # Django admin real no está expuesto. Solo paneles propios con roles.
        if request.path.startswith("/admin/"):
            return HttpResponseNotFound(
                "Administración Django no disponible en la demo."
            )

        if request.FILES:
            return HttpResponseForbidden(
                "La demostración no acepta documentos, fotos ni audios."
            )

        nombre = getattr(request.resolver_match, "url_name", "") or ""
        if nombre in {
            "registro",
            "verificar_correo",
            "consentimiento_tutor",
            "cargar_matriculas",
            "exportar_reporte_matriculas",
            "exportar_mis_datos",
        }:
            return HttpResponseForbidden(
                "Esta operación no está disponible en la demo pública."
            )

        # Desactivar recuperación/cambio de claves de las cuentas compartidas,
        # pero conservar login/logout para explorar los cuatro roles.
        if request.path.startswith("/accounts/") and nombre not in {
            "login", "logout"
        }:
            return HttpResponseForbidden(
                "No se pueden modificar credenciales en la demo pública."
            )

        if nombre.startswith("eliminar_"):
            return HttpResponseForbidden(
                "Las eliminaciones no están disponibles en la demo pública."
            )

        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            # Paneles administrativos y docentes navegables en modo lectura.
            rutas_lectura = (
                "/gestion/",
                "/admin_gestion_",
                "/gestion_acudientes_estudiantes/",
                "/panel-docente/",
                "/banco-preguntas/",
                "/perfil/",
                "/configuraciones/",
            )
            if request.path.startswith(rutas_lectura) or nombre.startswith(
                ("admin_", "editar_")
            ):
                return HttpResponseForbidden(
                    "Puedes consultar los paneles, pero no modificarlos "
                    "en esta demostración pública."
                )
        return None
