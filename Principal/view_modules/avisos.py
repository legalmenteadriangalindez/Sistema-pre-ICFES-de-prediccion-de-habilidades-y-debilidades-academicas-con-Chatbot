"""Bandeja privada de avisos y preferencias."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from Principal.models import NotificacionAcademica, PreferenciaAvisos


@login_required
@require_http_methods(["GET", "POST"])
def mis_avisos(request):
    preferencias, _ = PreferenciaAvisos.objects.get_or_create(
        usuario=request.user,
    )
    if request.method == "POST":
        if request.POST.get("accion") == "preferencias":
            preferencias.recibir_avisos = request.POST.get("recibir_avisos") == "on"
            preferencias.avisos_familiares = (
                request.POST.get("avisos_familiares") == "on"
            )
            preferencias.save()
            messages.success(request, "Preferencias de avisos guardadas.")
            return redirect("mis_avisos")
    avisos = NotificacionAcademica.objects.filter(
        usuario=request.user,
    )[:100]
    return render(request, "MisAvisos.html", {
        "avisos": avisos, "preferencias": preferencias,
    })


@login_required
@require_POST
def marcar_aviso_leido(request, aviso_id):
    aviso = get_object_or_404(
        NotificacionAcademica, pk=aviso_id, usuario=request.user,
    )
    if aviso.leida_en is None:
        aviso.leida_en = timezone.now()
        aviso.save(update_fields=["leida_en"])
    return redirect("mis_avisos")
