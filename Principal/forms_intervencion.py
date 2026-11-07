"""Formularios explícitos: no aceptar docente, historial o estado del POST."""
from django import forms
from django.utils import timezone

from Principal.models import IntervencionAcademica


class IntervencionForm(forms.ModelForm):
    class Meta:
        model = IntervencionAcademica
        fields = (
            "matricula", "materia", "competencia",
            "objetivo", "actividades", "fecha_revision",
        )
        widgets = {
            "matricula": forms.Select(attrs={"class": "form-select"}),
            "materia": forms.Select(attrs={"class": "form-select"}),
            "competencia": forms.TextInput(attrs={"class": "form-control"}),
            "objetivo": forms.TextInput(attrs={"class": "form-control"}),
            "actividades": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "fecha_revision": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, permitidas=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matricula"].queryset = (
            permitidas if permitidas is not None
            else IntervencionAcademica.objects.none()
        )

    def clean_fecha_revision(self):
        fecha = self.cleaned_data["fecha_revision"]
        if fecha < timezone.localdate():
            raise forms.ValidationError("La fecha de revisión no puede estar en el pasado.")
        return fecha

    def clean_competencia(self):
        texto = self.cleaned_data["competencia"].strip()
        if len(texto) < 3:
            raise forms.ValidationError("Especifica una competencia válida.")
        return texto
