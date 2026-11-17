"""Fachada de URLs de Principal organizada por área funcional.

El orden de las colecciones conserva las rutas públicas existentes. Las
aplicaciones externas siguen importando `Principal.urls.urlpatterns`.
"""

from .url_modules.account import urlpatterns as account_urlpatterns
from .url_modules.academico import urlpatterns as academic_urlpatterns
from .url_modules.admin import urlpatterns as admin_urlpatterns

urlpatterns = [
    *academic_urlpatterns,
    *admin_urlpatterns,
    *account_urlpatterns,
]
