from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Sexo, RelacionAcudiente, Acudiente,
    Grado, Curso, AnioLectivo,Materia,
    Nota, Boletin, Observacion,Persona,Estudiante,Rol,RitmoAprendizaje,
    EstiloAprendizaje,NivelAprendizaje,PerfilPedagogico,Riesgo,
    PrediccionRiesgo,Recomendacion,PreferenciaAccesibilidad,
    Tema,TemaAsignado, ProgresoTema,Actividad

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



class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "input-field"})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input-field"})
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "input-field",
            "placeholder": "Ingrese su contraseña"
        })
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "input-field",
            "placeholder": "Ingrese nuevamente su contraseña"
        })
    )
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input-field"}),
            "email": forms.EmailInput(attrs={"class": "input-field"}),
            "password1": forms.PasswordInput(attrs={"class": "input-field"})
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        exclude = ["user"]

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


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ["necesidades_especiales","persona"]

        widgets = {
            "necesidades_especiales": forms.Textarea(
                attrs={"class": "input-text-area", "rows": 3}
            ),
        }


class RolForm(forms.ModelForm):
    class Meta:
        model= Rol
        fields = ["nombre","descripcion"]

        widgets={
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "descripcion": forms.TextInput(attrs={"class": "input-field"})
        }

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
