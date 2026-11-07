"""Matrículas, vínculos familiares y reportes: solo administración."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from Principal.models import (
    Acudiente, ActividadAsignada, AnioLectivo, Curso, Estudiante,
    EstudianteAcudiente, IntentoEvaluacion, Matricula,
    RelacionAcudiente, RetroalimentacionDocente,
)
from .selectores import es_gestor


class MatriculaAdminForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ("estudiante", "curso", "anio_lectivo", "activa")
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "curso": forms.Select(attrs={"class": "form-select"}),
            "anio_lectivo": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        datos = super().clean()
        alumno = datos.get("estudiante")
        curso = datos.get("curso")
        anio = datos.get("anio_lectivo")
        activa = datos.get("activa")
        if alumno and anio and Matricula.objects.filter(
            estudiante=alumno, anio_lectivo=anio,
        ).exclude(pk=self.instance.pk).exists():
            self.add_error("estudiante", "Ya existe una matrícula de este estudiante en ese año. Edítala.")
        if curso and activa:
            if not curso.activo:
                self.add_error("curso", "El curso debe estar activo.")
            elif anio and Matricula.objects.filter(
                curso=curso, anio_lectivo=anio, activa=True,
            ).exclude(pk=self.instance.pk).count() >= curso.cupo_maximo:
                self.add_error("curso", "El curso alcanzó su cupo máximo para ese año.")
        return datos


class VinculoFamiliarAdminForm(forms.ModelForm):
    class Meta:
        model = EstudianteAcudiente
        fields = ("estudiante", "acudiente", "relacion")
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "acudiente": forms.Select(attrs={"class": "form-select"}),
            "relacion": forms.Select(attrs={"class": "form-select"}),
        }


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def gestion_matriculas_familias(request):
    form_matricula = MatriculaAdminForm()
    form_vinculo = VinculoFamiliarAdminForm()
    if request.method == "POST":
        tipo = request.POST.get("tipo")
        if tipo == "matricula":
            form_matricula = MatriculaAdminForm(request.POST)
            if form_matricula.is_valid():
                with transaction.atomic():
                    Curso.objects.select_for_update().get(pk=form_matricula.cleaned_data["curso"].pk)
                    # Validación adicional bajo bloqueo en motores que lo admiten.
                    form_matricula.full_clean()
                    if form_matricula.is_valid():
                        form_matricula.save()
                        messages.success(request, "Matrícula creada correctamente.")
                        return redirect("admin_matriculas_familias")
        elif tipo == "vinculo":
            form_vinculo = VinculoFamiliarAdminForm(request.POST)
            if form_vinculo.is_valid():
                form_vinculo.save()
                messages.success(request, "Vínculo familiar registrado.")
                return redirect("admin_matriculas_familias")

    matriculas = Matricula.objects.select_related(
        "estudiante__persona", "curso__grado", "anio_lectivo",
    ).order_by("-anio_lectivo__anio", "estudiante__persona__apellido")[:300]
    vinculos = EstudianteAcudiente.objects.select_related(
        "estudiante__persona", "acudiente__persona", "relacion",
    ).order_by("estudiante__persona__apellido")[:300]
    return render(request, "AdminMatriculasFamilias.html", {
        "form_matricula": form_matricula, "form_vinculo": form_vinculo,
        "matriculas": matriculas, "vinculos": vinculos,
    })


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def editar_matricula(request, matricula_id):
    matricula = get_object_or_404(Matricula, pk=matricula_id)
    formulario = MatriculaAdminForm(
        request.POST if request.method == "POST" else None, instance=matricula,
    )
    if request.method == "POST" and formulario.is_valid():
        with transaction.atomic():
            Curso.objects.select_for_update().get(pk=formulario.cleaned_data["curso"].pk)
            formulario.full_clean()
            if formulario.is_valid():
                formulario.save()
                messages.success(request, "Matrícula actualizada.")
                return redirect("admin_matriculas_familias")
    return render(request, "AdminEditarRegistro.html", {
        "titulo": "Editar matrícula", "formulario": formulario,
        "volver": "admin_matriculas_familias",
    })


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def editar_vinculo_familiar(request, vinculo_id):
    vinculo = get_object_or_404(EstudianteAcudiente, pk=vinculo_id)
    formulario = VinculoFamiliarAdminForm(
        request.POST if request.method == "POST" else None, instance=vinculo,
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Vínculo actualizado.")
        return redirect("admin_matriculas_familias")
    return render(request, "AdminEditarRegistro.html", {
        "titulo": "Editar vínculo familiar", "formulario": formulario,
        "volver": "admin_matriculas_familias",
    })


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_POST
def desvincular_familiar(request, vinculo_id):
    vinculo = get_object_or_404(EstudianteAcudiente, pk=vinculo_id)
    vinculo.delete()
    messages.success(request, "Vínculo eliminado. El acudiente perdió ese acceso.")
    return redirect("admin_matriculas_familias")


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET"])
def reportes_academicos_admin(request):
    """Resumen descriptivo, sin atribuir intentos históricos a un año concreto."""
    matriculas = Matricula.objects.filter(activa=True)
    grupos = matriculas.values(
        "curso_id", "anio_lectivo_id", "curso__grado__nombre", "curso__nombre",
        "anio_lectivo__anio",
    ).annotate(alumnos=Count("estudiante_id", distinct=True)).order_by(
        "anio_lectivo__anio", "curso__grado__nombre", "curso__nombre",
    )
    filas = []
    for g in grupos:
        estudiantes = matriculas.filter(
            curso_id=g["curso_id"], anio_lectivo_id=g["anio_lectivo_id"],
        ).values_list("estudiante_id", flat=True)
        acumulado = IntentoEvaluacion.objects.filter(
            estudiante_id__in=estudiantes,
        ).aggregate(intentos=Count("id"), aciertos=Sum("aciertos"), preguntas=Sum("total_preguntas"))
        preguntas = acumulado["preguntas"] or 0
        filas.append({
            **g, "intentos": acumulado["intentos"],
            "porcentaje": round(100 * (acumulado["aciertos"] or 0) / preguntas, 1)
            if preguntas else None,
        })
    return render(request, "AdminReportesAcademicos.html", {
        "filas": filas,
        "total_matriculas_activas": matriculas.count(),
        "total_evaluaciones": IntentoEvaluacion.objects.count(),
        "total_asignaciones": ActividadAsignada.objects.count(),
        "total_completadas": ActividadAsignada.objects.filter(completada=True).count(),
        "total_retroalimentaciones": RetroalimentacionDocente.objects.count(),
    })
