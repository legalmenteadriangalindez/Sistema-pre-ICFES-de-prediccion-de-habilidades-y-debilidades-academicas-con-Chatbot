"""Permite distinguir el demo público en cualquier plantilla sin alterar el modo local."""
from django.conf import settings


def estado_demo(request):
    return {"demo_mode": settings.DEMO_MODE}
