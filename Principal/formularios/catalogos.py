"""Formularios para catálogos y relaciones familiares."""

from django import forms

from ..models import (
    Acudiente,
    AnioLectivo,
    Curso,
    Estudiante,
    Grado,
    Materia,
    Persona,
    RelacionAcudiente,
    Rol,
    Sexo,
)


class SexoForm(forms.ModelForm):
    class Meta:
        model = Sexo
        exclude = ['codigo']
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class RelacionAcudienteForm(forms.ModelForm):
    class Meta:
        model = RelacionAcudiente
        exclude = ['codigo']
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class GradoForm(forms.ModelForm):
    class Meta:
        model = Grado
        exclude = ['codigo']
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class AnioLectivoForm(forms.ModelForm):
    class Meta:
        model = AnioLectivo
        fields = "__all__"
        widgets = {
            "anio": forms.NumberInput(attrs={"class": "input-field"}),
            "fecha_inicio": forms.DateInput(attrs={
                "type": "date", "class": "input-field"
            }),
            "fecha_fin": forms.DateInput(attrs={
                "type": "date", "class": "input-field"
            }),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class AcudienteForm(forms.ModelForm):
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.all(),
        empty_label="Seleccione una persona"
        )
    class Meta:
        model = Acudiente
        fields = ["persona"]
        
        widgets = {
            "persona": forms.Select(attrs={"class": "input-select"}),
            "relacion": forms.Select(attrs={"class": "input-select"}),
        }


class AsignarAcudienteForm(forms.Form):
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.filter(estudianteacudiente__isnull=True),
        label="Estudiante",
        empty_label="Seleccione un estudiante",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    acudiente = forms.ModelChoiceField(
        queryset=Acudiente.objects.all(),
        label="Acudiente",
        empty_label="Seleccione un acudiente",
        widget=forms.Select(attrs={"class": "form-select"})
    )


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = "__all__"
        widgets = {
            "grado": forms.Select(attrs={"class": "input-select"}),
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "cupo_maximo": forms.NumberInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        exclude = ['codigo']
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class RolForm(forms.ModelForm):
    class Meta:
        model= Rol
        fields = ["nombre","descripcion"]

        widgets={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})
        }