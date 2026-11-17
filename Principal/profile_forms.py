"""Formularios independientes para actualizar la cuenta y el perfil propio.

Estos formularios no reutilizan el formulario de registro: el registro necesita
contraseñas nuevas, mientras que la edición de perfil solo modifica los datos
que pertenecen al usuario autenticado.
"""

from django import forms
from django.contrib.auth.models import User

from .models import Estudiante, Persona


class UserProfileUpdateForm(forms.ModelForm):
    """Datos de la cuenta que el usuario puede actualizar por sí mismo."""

    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "email",
                "placeholder": "Escribe tu correo electrónico",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombres",
            "last_name": "Apellidos",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "username",
                    "placeholder": "Escribe tu nombre de usuario",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "given-name",
                    "placeholder": "Escribe tus nombres",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "family-name",
                    "placeholder": "Escribe tus apellidos",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Este correo electrónico ya está registrado."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        if commit:
            user.save()
        return user


class PersonaProfileUpdateForm(forms.ModelForm):
    """Datos personales; nunca expone la relación con el perfil de usuario."""

    class Meta:
        model = Persona
        fields = (
            "nombre",
            "apellido",
            "documento",
            "fecha_nacimiento",
            "direccion",
            "telefono",
            "sexo",
        )
        labels = {
            "nombre": "Nombres",
            "apellido": "Apellidos",
            "documento": "Documento",
            "fecha_nacimiento": "Fecha de nacimiento",
            "direccion": "Dirección",
            "telefono": "Teléfono",
            "sexo": "Sexo",
        }
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "given-name",
                    "placeholder": "Escribe tus nombres",
                }
            ),
            "apellido": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "family-name",
                    "placeholder": "Escribe tus apellidos",
                }
            ),
            "documento": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "off",
                    "placeholder": "Escribe tu documento",
                }
            ),
            "fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "auth-input"},
            ),
            "direccion": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "street-address",
                    "placeholder": "Escribe tu dirección",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "auth-input",
                    "autocomplete": "tel",
                    "placeholder": "Escribe tu teléfono",
                }
            ),
            "sexo": forms.Select(attrs={"class": "auth-input"}),
        }


class EstudianteProfileUpdateForm(forms.ModelForm):
    """Preferencias académicas propias, sin permitir cambiar la persona."""

    class Meta:
        model = Estudiante
        fields = ("necesidades_especiales",)
        labels = {
            "necesidades_especiales": "Necesidades especiales o apoyos",
        }
        widgets = {
            "necesidades_especiales": forms.Textarea(
                attrs={
                    "class": "auth-input",
                    "rows": 4,
                    "placeholder": "Escribe información que debamos tener en cuenta",
                }
            )
        }
