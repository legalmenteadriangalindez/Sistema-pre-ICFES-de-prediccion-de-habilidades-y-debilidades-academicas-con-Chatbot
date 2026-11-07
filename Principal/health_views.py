"""Health checks sin datos personales, credenciales ni detalles de errores."""
from django.db import connection
from django.db.utils import DatabaseError, InterfaceError, OperationalError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def healthz(request):
    """Liveness: el proceso Django puede responder."""
    return JsonResponse({"status": "alive"})


@never_cache
@require_GET
def readyz(request):
    """Readiness: Django está conectado a la base persistente."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except (DatabaseError, InterfaceError, OperationalError):
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
