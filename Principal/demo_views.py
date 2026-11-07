"""Portada pública sin acceso a datos de personas reales."""
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def demo_publica(request):
    return render(request, "DemoPublica.html")
