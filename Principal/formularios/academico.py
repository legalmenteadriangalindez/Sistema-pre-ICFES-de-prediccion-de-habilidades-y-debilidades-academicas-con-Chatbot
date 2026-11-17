"""Formularios de personas, matrículas y resultados académicos."""

from django import forms

from ..models import Boletin, Estudiante, Nota, Observacion, Persona


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select auth-input"}),
            "asignacion": forms.Select(attrs={"class": "input-select auth-input"}),
            "valor": forms.NumberInput(attrs={"class": "input-field auth-input"}),
        }


class BoletinForm(forms.ModelForm):
    class Meta:
        model = Boletin
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select auth-input"}),
            "promedio_periodo": forms.NumberInput(attrs={"class": "input-field auth-input"}),
            "observaciones_generales": forms.Textarea(
                attrs={"class": "input-text-area auth-input", "rows": 3}
            ),
        }


class ObservacionForm(forms.ModelForm):
    class Meta:
        model = Observacion
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select auth-input"}),
            "asignacion": forms.Select(attrs={"class": "input-select auth-input"}),
            "texto": forms.Textarea(
                attrs={"class": "input-text-area auth-input", "rows": 3}
            ),
        }


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        exclude = ["perfil_user"]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "apellido": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "documento": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "input-field auth-input"}
            ),
            "direccion": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "telefono": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "sexo": forms.Select(attrs={"class": "input-select auth-input"}),
        }


class RegistroEstudianteForm(forms.ModelForm):
    """Registro público: la persona se vincula en la vista, nunca desde el navegador."""
    class Meta:
        model = Estudiante
        fields = ["necesidades_especiales"]
        widgets = {"necesidades_especiales": forms.Textarea(attrs={"class": "input-text-area auth-input", "rows": 3})}


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ["necesidades_especiales","persona"]

        widgets = {
            "necesidades_especiales": forms.Textarea(
                attrs={"class": "input-text-area auth-input", "rows": 3}
            ),
        }