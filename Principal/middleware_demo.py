"""Cierre de operaciones sensibles de la demostración gratuita.

Los usuarios y los datos del demo son sintéticos; no permitir altas reales,
archivos, administración, correos ni cambios de identidad en instancia pública.
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

        if request.path.startswith("/admin/"):
            return HttpResponseNotFound("Administración no disponible en la demo.")

        if request.FILES:
            return HttpResponseForbidden(
                "La demostración no acepta documentos, fotos ni audios."
            )

        nombre = getattr(request.resolver_match, "url_name", "") or ""
        cerradas = {
            "registro", "verificar_correo", "admin_gestion_users",
            "admin_gestion_db", "admin_gestion_academica",
            "admin_matriculas_familias", "cargar_matriculas",
            "admin_reportes_academicos", "exportar_reporte_matriculas",
            "admin_asignaciones_docentes", "admin_editar_usuario",
            "admin_editar_persona", "admin_editar_necesidades_estudiante",
            "admin_editar_catalogo", "intervenciones_docente",
            "editar_actividad_docente", "editar_matricula",
            "exportar_mis_datos", "consentimiento_tutor",
        }
        if nombre in cerradas or request.path.startswith("/gestion/"):
            return HttpResponseForbidden(
                "La administración y el registro no están disponibles "
                "en la demostración pública."
            )

        if request.method not in {"GET", "HEAD", "OPTIONS"} and (
            nombre.startswith("eliminar_")
            or request.path.startswith("/perfil/")
            or request.path.startswith("/configuraciones/")
        ):
            return HttpResponseForbidden(
                "Los cambios de identidad no se permiten en la demo."
            )
        return None
