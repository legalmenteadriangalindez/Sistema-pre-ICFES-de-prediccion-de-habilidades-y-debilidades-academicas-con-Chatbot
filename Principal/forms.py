from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Estudiante



class UserRegisterForm(UserCreationForm):
    # email = forms.EmailField(required=True)

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "input-field"})
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
        }

class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        exclude = ["user"]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input-field"}),
            "apellido": forms.TextInput(attrs={"class": "input-field"}),
            "documento": forms.TextInput(attrs={"class": "input-field"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "input-field"}
            ),
            "email": forms.EmailInput(attrs={"class": "input-field"}),
            "direccion": forms.TextInput(attrs={"class": "input-field"}),
            "telefono": forms.TextInput(attrs={"class": "input-field"}),
            "grado": forms.TextInput(attrs={"class": "input-field"}),
            "sexo": forms.Select(attrs={"class": "input-select"}),
            "acudiente": forms.Select(attrs={"class": "input-select"}),
            "necesidades_especiales": forms.Textarea(
                attrs={"class": "input-text-area", "rows": 3}
            ),
            "docentes": forms.Select(attrs={"class": "input-select"}),
            "promedio": forms.NumberInput(attrs={"class": "input-field"})
        }

