"""Gestión administrativa de estudiantes y acudientes."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Principal.forms import AcudienteForm, EstudianteForm
from Principal.models import Acudiente, Estudiante
from .selectores import es_gestor
from .admin_operaciones import eliminar_si_no_referenciado

@login_required # @user_passes_test(es_coordinador)
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_acudientes_estudiantes(request):
    estudiantes = Estudiante.objects.all()
    acudientes = Acudiente.objects.all()
    if request.method == "POST":
        tipo_form= request.POST.get("form")
        if tipo_form == "estudiantes":
            form_estudiantes = EstudianteForm(request.POST)
            if form_estudiantes.is_valid():
                form_estudiantes.save()
                return redirect('gestion_acudientes_estudiantes')
        else:
            form_estudiantes = EstudianteForm(request.POST)
        if tipo_form == "acudientes":
            form_acudientes = AcudienteForm(request.POST)
            if form_acudientes.is_valid():
               form_acudientes.save()
               return redirect('gestion_acudientes_estudiantes')
        else:
           form_acudientes = AcudienteForm()
    else :
        form_estudiantes = EstudianteForm()
        form_acudientes = AcudienteForm()
    contexto = {
        "estudiantes": estudiantes,
        "acudientes": acudientes,
        "form_estudiantes": form_estudiantes,
        "form_acudientes": form_acudientes
    }
    return render(request, "gestion_estudiantes_acudientes.html", contexto)


@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
@require_POST
def eliminar_gestion_acudientes_estudiantes(request, tipo, id):
    tipos = {"estudiantes": Estudiante, "acudientes": Acudiente}
    if tipo not in tipos:
        from django.http import Http404
        raise Http404("Tipo no reconocido.")
    objeto = get_object_or_404(tipos[tipo], pk=id)
    if eliminar_si_no_referenciado(objeto):
        messages.success(request, "Registro eliminado.")
    else:
        messages.error(request, "No se puede eliminar un estudiante/acudiente con relaciones vigentes. Desactiva o desvincula primero.")
    return redirect("gestion_acudientes_estudiantes")
