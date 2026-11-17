"""Formularios de aprendizaje, riesgo y práctica adaptativa."""

from django import forms

from ..models import (
    Actividad,
    EstiloAprendizaje,
    NivelAprendizaje,
    PerfilPedagogico,
    PreferenciaAccesibilidad,
    PrediccionRiesgo,
    Recomendacion,
    Riesgo,
    RitmoAprendizaje,
    ProgresoTema,
    Tema,
    TemaAsignado,
)


class RitmoAprendizajeForm(forms.ModelForm):
    class Meta:
        model =RitmoAprendizaje 
        fields = ["nombre","descripcion"]

        widgets ={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})            
        }


class EstiloAprendizajeForm(forms.ModelForm):
    class Meta:
        model = EstiloAprendizaje
        fields = ["nombre","descripcion"]

        widgets ={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})            
        }


class NivelAprendizajeForm(forms.ModelForm):
    class Meta:
        model = NivelAprendizaje
        fields = ["nombre","descripcion"]

        widgets ={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})            
        }


class PerfilPedagogicoForm(forms.ModelForm):
    class Meta:
        model= PerfilPedagogico
        fields = ["estudiante","ritmo","estilo","nivel"]

        widgets ={
            "estudiante": forms.Select(attrs={"class": "input-select"}),
            "ritmo": forms.Select(attrs={"class": "input-select"}),
            "estilo": forms.Select(attrs={"class": "input-select"}),
            "nivel": forms.Select(attrs={"class": "input-select"})
        }


class RiesgoForm(forms.ModelForm):
    class Meta:
        model = Riesgo
        fields = ["nombre","descripcion"]

        widgets ={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})            
        }


class PrediccionRiesgoForm(forms.ModelForm):
    class Meta:
        model = PrediccionRiesgo
        fields = ["riesgo","probabilidad"]

        widgets = {
            "riesgo": forms.Select(attrs={"class": "input-select"}),
            "probabilidad" : forms.NumberInput(attrs={"step": "0.01"})
        }


class RecomendacionForm(forms.ModelForm):
    class Meta:
        model = Recomendacion
        fields = ["matricula","texto"]

        widgets ={
            "matricula": forms.Select(attrs={"class": "input-select"}),
            "texto": forms.TextInput(attrs={"class": "input-field"})
        }


class PreferenciaAccesibilidadForm(forms.ModelForm):
    class Meta:
        model= PreferenciaAccesibilidad
        fields = ["necesita_audio","necesita_visual","necesita_texto_simple"]

        widgets ={
            "necesita_audio": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
            "necesita_visual" : forms.CheckboxInput(attrs={"class": "input-checkbox"}),
            "necesita_texto_simple": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class TemaForm(forms.ModelForm):
    class Meta:
        model = Tema
        fields = ["nombre","descripcion"]

        widgets ={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})            
        }


class TemaAsignadoForm(forms.ModelForm):
    class Meta:
        model = TemaAsignado

        fields = ["estudiante","tema"]

        widgets = {
            "estudiante": forms.Select(attrs={"class": "input-select"}),
            "tema": forms.Select(attrs={"class": "input-select"}),
        }


class ProgresoTemaForm(forms.ModelForm):
    class Meta:
        model = ProgresoTema
        fields = ["tema_asignado","porcentaje","nivel"]

        widgets ={
            "tema_asignado": forms.Select(attrs={"class": "input-select"}),
            "porcentaje": forms.NumberInput(attrs={"class": "input-field"}),
            "nivel": forms.Select(attrs={"class": "input-select"}),
        }


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ["tema","titulo","descripcion","nivel","activo"]

        widgets = {
            "tema": forms.Select(attrs={"class": "input-select"}),
            "titulo":  forms.TextInput(attrs={"class": "input-field"}),
            "descripcion" : forms.Textarea(attrs={"class": "input-area"}), 
            "nivel" : forms.Select(attrs={"class": "input-select"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"})
        }