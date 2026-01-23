from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Sexo, RelacionAcudiente, Acudiente, Docente,
    Grado, Jornada, Curso, Sede, AnioLectivo,
    Materia, AsignacionDocente, PeriodoAcademico,
    Nota, Boletin, Observacion,Persona,Estudiante,Rol
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


class JornadaForm(forms.ModelForm):
    class Meta:
        model = Jornada
        exclude = ['codigo']
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        exclude = ['codigo']
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "direccion": forms.TextInput(attrs={"class": "input-field"}),
            "telefono": forms.TextInput(attrs={"class": "input-field"}),
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
    class Meta:
        model = Acudiente
        fields = ["persona", "relacion"]
        persona = forms.ModelChoiceField(
        queryset=Persona.objects.all(),
        empty_label="Seleccione una persona"
        )
        widgets = {
            "persona": forms.Select(attrs={"class": "input-select"}),
            "relacion": forms.Select(attrs={"class": "input-select"}),
        }

class AsignarAcudienteForm(forms.Form):
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.filter(acudiente__isnull=True),
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

class DocenteForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ["persona"]
        widgets = {
            "persona": forms.Select(attrs={"class": "input-select"}),
        }


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = "__all__"
        widgets = {
            "grado": forms.Select(attrs={"class": "input-select"}),
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "jornada": forms.Select(attrs={"class": "input-select"}),
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


class AsignacionDocenteForm(forms.ModelForm):
    class Meta:
        model = AsignacionDocente
        fields = "__all__"
        widgets = {
            "docente": forms.Select(attrs={"class": "input-select"}),
            "curso": forms.Select(attrs={"class": "input-select"}),
            "materia": forms.Select(attrs={"class": "input-select"}),
            "anio_lectivo": forms.Select(attrs={"class": "input-select"}),
            "sede": forms.Select(attrs={"class": "input-select"}),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class PeriodoAcademicoForm(forms.ModelForm):
    class Meta:
        model = PeriodoAcademico
        fields = "__all__"
        widgets = {
            "numero": forms.NumberInput(attrs={"class": "input-field"}),
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "anio_lectivo": forms.Select(attrs={"class": "input-select"}),
            "fecha_inicio": forms.DateInput(attrs={
                "type": "date", "class": "input-field"
            }),
            "fecha_fin": forms.DateInput(attrs={
                "type": "date", "class": "input-field"
            }),
            "activo": forms.CheckboxInput(attrs={"class": "input-checkbox"}),
        }


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"
        widgets = {
            "estudiante": forms.Select(attrs={"class": "input-select"}),
            "asignacion": forms.Select(attrs={"class": "input-select"}),
            "periodo": forms.Select(attrs={"class": "input-select"}),
            "valor": forms.NumberInput(attrs={"class": "input-field"}),
        }


class BoletinForm(forms.ModelForm):
    class Meta:
        model = Boletin
        fields = "__all__"
        widgets = {
            "estudiante": forms.Select(attrs={"class": "input-select"}),
            "periodo": forms.Select(attrs={"class": "input-select"}),
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
            "estudiante": forms.Select(attrs={"class": "input-select"}),
            "asignacion": forms.Select(attrs={"class": "input-select"}),
            "periodo": forms.Select(attrs={"class": "input-select"}),
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
        fields = ["curso", "acudiente", "necesidades_especiales"]

        widgets = {
            "curso": forms.Select(attrs={"class": "input-select"}),
            "acudiente": forms.Select(attrs={"class": "input-select"}),
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
