"""Edición administrativa segura y catálogo referenciado sin borrado en cascada."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError, RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from Principal.forms import (
    AnioLectivoForm, CursoForm, GradoForm, MateriaForm, PersonaForm,
    RelacionAcudienteForm, RolForm, SexoForm,
)
from Principal.models import (
    AnioLectivo, Curso, Grado, Materia, PerfilUsuario, Persona,
    RelacionAcudiente, Rol, Sexo,
)
from .selectores import es_gestor


class CrearPersonaAdminForm(PersonaForm):
    """No permitir crear una Persona sin relacionarla con una cuenta."""
    perfil_user = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.none(),
        label="Cuenta de usuario",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(PersonaForm.Meta):
        fields = (
            "perfil_user", "nombre", "apellido", "documento",
            "fecha_nacimiento", "direccion", "telefono", "sexo",
        )
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["perfil_user"].queryset = PerfilUsuario.objects.filter(
            persona__isnull=True,
        ).select_related("user").order_by("user__username")


class EditarUsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk,
        ).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email


CATALOGOS = {
    "grados": (Grado, GradoForm, "admin_gestion_academica"),
    "cursos": (Curso, CursoForm, "admin_gestion_academica"),
    "anios": (AnioLectivo, AnioLectivoForm, "admin_gestion_academica"),
    "materias": (Materia, MateriaForm, "admin_gestion_academica"),
    "roles": (Rol, RolForm, "admin_gestion_db"),
    "sexos": (Sexo, SexoForm, "admin_gestion_db"),
    "relaciones": (RelacionAcudiente, RelacionAcudienteForm, "admin_gestion_db"),
}


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if usuario.is_superuser and not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("La edición de un superusuario está restringida.")
    formulario = EditarUsuarioAdminForm(
        request.POST if request.method == "POST" else None, instance=usuario,
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Cuenta actualizada correctamente.")
        return redirect("admin_gestion_users")
    return render(request, "AdminEditarRegistro.html", {
        "titulo": "Editar usuario", "formulario": formulario,
        "volver": "admin_gestion_users",
    })


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def editar_persona(request, persona_id):
    persona = get_object_or_404(Persona, pk=persona_id)
    formulario = PersonaForm(
        request.POST if request.method == "POST" else None, instance=persona,
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Persona actualizada correctamente.")
        return redirect("admin_gestion_users")
    return render(request, "AdminEditarRegistro.html", {
        "titulo": "Editar persona", "formulario": formulario,
        "volver": "admin_gestion_users",
    })


@login_required
@user_passes_test(es_gestor, login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def editar_catalogo(request, tipo, registro_id):
    if tipo not in CATALOGOS:
        from django.http import Http404
        raise Http404("Catálogo desconocido.")
    modelo, form_class, volver = CATALOGOS[tipo]
    objeto = get_object_or_404(modelo, pk=registro_id)
    formulario = form_class(
        request.POST if request.method == "POST" else None, instance=objeto,
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Registro académico actualizado.")
        return redirect(volver)
    return render(request, "AdminEditarRegistro.html", {
        "titulo": "Editar " + tipo, "formulario": formulario, "volver": volver,
    })


def eliminar_si_no_referenciado(objeto):
    """Bloquea cascadas silenciosas sobre matrículas, usuarios o asignaciones.

    Se reutiliza en los endpoints DELETE/POST heredados; la comprobación se
    efectúa dentro de la transacción y con las restricciones del esquema.
    """
    try:
        with transaction.atomic():
            for relacion in objeto._meta.related_objects:
                referencia = {relacion.field.name: objeto}
                if relacion.related_model._base_manager.filter(**referencia).exists():
                    return False
            objeto.delete()
        return True
    except (ProtectedError, RestrictedError, IntegrityError):
        return False
