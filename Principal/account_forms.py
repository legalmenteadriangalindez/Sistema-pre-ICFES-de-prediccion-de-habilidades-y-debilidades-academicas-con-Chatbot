"""Formularios de inicio de sesión y administración de contraseña."""
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class PreICFESAuthenticationForm(AuthenticationForm):
    """Conserva la autenticación de Django y añade etiquetas para los navegadores."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update({
            "class": "auth-input",
            "autocomplete": "username",
            "autocapitalize": "none",
            "spellcheck": "false",
            "placeholder": "Escribe tu usuario",
        })
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update({
            "class": "auth-input",
            "autocomplete": "current-password",
            "placeholder": "Escribe tu contraseña",
        })


class PreICFESPasswordChangeForm(PasswordChangeForm):
    """Mantiene las validaciones de Django y marca cada propósito de contraseña."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "old_password": "Contraseña actual",
            "new_password1": "Nueva contraseña",
            "new_password2": "Confirmar nueva contraseña",
        }
        autocomplete = {
            "old_password": "current-password",
            "new_password1": "new-password",
            "new_password2": "new-password",
        }
        placeholders = {
            "old_password": "Escribe tu contraseña actual",
            "new_password1": "Escribe una contraseña nueva",
            "new_password2": "Repite la contraseña nueva",
        }
        for name, label in labels.items():
            field = self.fields[name]
            field.label = label
            field.widget.attrs.update({
                "class": "auth-input",
                "autocomplete": autocomplete[name],
                "placeholder": placeholders[name],
            })
