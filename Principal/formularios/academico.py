"""Formularios de personas, matrículas y resultados académicos."""

from django import forms

from ..models import Boletin, Estudiante, Nota, Observacion, Persona


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select"}),
            "asignacion": forms.Select(attrs={"class": "input-select"}),
            "valor": forms.NumberInput(attrs={"class": "input-field"}),
        }


class BoletinForm(forms.ModelForm):
    class Meta:
        model = Boletin
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select"}),
            "promedio_periodo": forms.NumberInput(attrs={"class": "input-field"}),
            "observaciones_generales": forms.Textarea(
                attrs={"class": "input-text-area", "rows": 3}
            ),
        }


class ObservacionForm(forms.ModelForm):
    class Meta:
        model = Observacion
        fields = "__all__"
        widgets = {
            "matricula": forms.Select(attrs={"class": "input-select"}),
            "asignacion": forms.Select(attrs={"class": "input-select"}),
            "texto": forms.Textarea(
                attrs={"class": "input-text-area", "rows": 3}
            ),
        }


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        exclude = ["perfil_user"]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "apellido": forms.TextInput(attrs={"class": "input-field"}),
            "documento": forms.TextInput(attrs={"class": "input-field"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "input-field"}
            ),
            "direccion": forms.TextInput(attrs={"class": "input-field"}),
            "telefono": forms.TextInput(attrs={"class": "input-field"}),
            "sexo": forms.Select(attrs={"class": "input-select"}),
        }


class RegistroEstudianteForm(forms.ModelForm):
    """Registro público: la persona se vincula en la vista, nunca desde el navegador."""
    class Meta:
        model = Estudiante
        fields = ["necesidades_especiales"]
        widgets = {"necesidades_especiales": forms.Textarea(attrs={"class": "input-text-area", "rows": 3})}


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ["necesidades_especiales","persona"]

        widgets = {
            "necesidades_especiales": forms.Textarea(
                attrs={"class": "input-text-area", "rows": 3}
            ),
        }