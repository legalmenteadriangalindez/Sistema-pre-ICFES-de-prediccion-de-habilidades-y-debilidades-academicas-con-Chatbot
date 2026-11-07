"""Formulario del banco: reconstruye las cuatro opciones desde campos fiables."""
from django import forms

from Principal.models import PreguntaBanco


class PreguntaBancoForm(forms.ModelForm):
    opcion_a = forms.CharField(max_length=500, label="Opción A")
    opcion_b = forms.CharField(max_length=500, label="Opción B")
    opcion_c = forms.CharField(max_length=500, label="Opción C")
    opcion_d = forms.CharField(max_length=500, label="Opción D")
    # El contenido enviado en este campo es ignorado: las opciones se
    # reconstruyen exclusivamente con los cuatro campos editables.
    opciones = forms.JSONField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = PreguntaBanco
        fields = (
            "materia", "competencia", "evidencia", "dificultad", "contexto", "enunciado",
            "opcion_a", "opcion_b", "opcion_c", "opcion_d", "opciones",
            "respuesta_correcta", "explicacion",
        )
        widgets = {
            "materia": forms.Select(attrs={"class": "form-select"}),
            "competencia": forms.TextInput(attrs={"class": "form-control"}),
            "evidencia": forms.TextInput(attrs={"class": "form-control", "placeholder": "Evidencia de aprendizaje asociada"}),
            "dificultad": forms.Select(attrs={"class": "form-select"}),
            "contexto": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "enunciado": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "respuesta_correcta": forms.Select(
                choices=[(letra, letra) for letra in ("A", "B", "C", "D")],
                attrs={"class": "form-select"},
            ),
            "explicacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for letra in ("A", "B", "C", "D"):
            self.fields["opcion_" + letra.lower()].widget.attrs["class"] = "form-control"
            if self.instance.pk:
                self.fields["opcion_" + letra.lower()].initial = (
                    self.instance.opciones or {}
                ).get(letra, "")

    def clean(self):
        datos = super().clean()
        if all(datos.get("opcion_" + letra.lower()) for letra in "ABCD"):
            datos["opciones"] = {
                letra: datos["opcion_" + letra.lower()].strip() for letra in "ABCD"
            }
        return datos
