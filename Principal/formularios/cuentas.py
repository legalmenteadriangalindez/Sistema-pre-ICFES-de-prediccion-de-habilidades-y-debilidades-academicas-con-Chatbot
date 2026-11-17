"""Formularios de creación de cuentas."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "input-field auth-input"})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input-field auth-input"})
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "input-field auth-input",
            "placeholder": "Ingrese su contraseña"
        })
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "input-field auth-input",
            "placeholder": "Ingrese nuevamente su contraseña"
        })
    )
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input-field auth-input"}),
            "email": forms.EmailInput(attrs={"class": "input-field auth-input"}),
            "password1": forms.PasswordInput(attrs={"class": "input-field auth-input"})
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user