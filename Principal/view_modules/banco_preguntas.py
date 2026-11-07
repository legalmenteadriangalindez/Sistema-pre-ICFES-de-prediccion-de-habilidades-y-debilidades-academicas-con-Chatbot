"""Panel del banco: creación, moderación humana y borradores de IA."""
import logging

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from Principal.models import PreguntaBanco
from Principal.services.evaluaciones import normalizar_preguntas
from .docentes import matriculas_permitidas_docente
from .selectores import _tiene_rol, es_gestor

logger = logging.getLogger(__name__)


def puede_curaduría(user):
    """Solo administradores o docentes con matrículas autorizadas vigentes."""
    return es_gestor(user) or (
        _tiene_rol(user, "DOCENTE") and matriculas_permitidas_docente(user).exists()
    )


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


def generar_borrador_ia(materia, usuario):
    """La IA solo propone un borrador, nunca lo publica sin revisión humana."""
    from Principal.services.gestion_view_test import generar_quizes

    entradas = generar_quizes(materia, 1)
    normalizadas = normalizar_preguntas(entradas, materia)
    pregunta = normalizadas[0]
    opciones = pregunta["opciones"]
    if set(opciones) != {"A", "B", "C", "D"}:
        raise ValueError("La IA no devolvió cuatro alternativas completas.")

    objeto = PreguntaBanco(
        materia=materia, competencia=pregunta["competencia"][:100],
        evidencia="",  # El revisor humano puede completar la evidencia.
        dificultad="MEDIA", contexto=pregunta["contexto"][:5000],
        enunciado=pregunta["pregunta"][:2000],
        opciones=opciones,
        respuesta_correcta=pregunta["respuesta_correcta"],
        explicacion=pregunta["explicacion"][:2000],
        origen="IA", creado_por=usuario, estado="BORRADOR",
    )
    objeto.huella = objeto.generar_huella(objeto.materia, objeto.enunciado)
    objeto.full_clean()
    with transaction.atomic():
        objeto.save()
    return objeto


@login_required
@require_http_methods(["GET", "POST"])
def banco_preguntas(request):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes acceso a la curaduría de preguntas.")

    formulario = PreguntaBancoForm()
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion == "crear":
            formulario = PreguntaBancoForm(request.POST)
            if formulario.is_valid():
                objeto = formulario.save(commit=False)
                objeto.creado_por = request.user
                objeto.origen = "DOCENTE"
                objeto.estado = "BORRADOR"
                try:
                    with transaction.atomic():
                        objeto.save()
                except IntegrityError:
                    formulario.add_error("enunciado", "Ya existe una pregunta idéntica.")
                else:
                    messages.success(request, "Pregunta guardada en borrador.")
                    return redirect("banco_preguntas")
        elif accion == "generar_ia":
            materia = request.POST.get("materia", "")
            if materia not in dict(PreguntaBanco.MATERIAS):
                messages.error(request, "Selecciona una materia válida.")
            else:
                try:
                    objeto = generar_borrador_ia(materia, request.user)
                except Exception:
                    logger.exception("Error al crear borrador sugerido por IA")
                    messages.error(
                        request, "No se pudo generar un borrador válido. Comprueba Ollama o intenta de nuevo."
                    )
                else:
                    messages.success(request, "Borrador IA guardado; necesita revisión humana.")
                    return redirect("editar_pregunta_banco", pregunta_id=objeto.pk)
        else:
            raise Http404("Acción no disponible.")

    mias = PreguntaBanco.objects.filter(creado_por=request.user)[:100]
    pendientes = PreguntaBanco.objects.filter(estado="EN_REVISION").exclude(
        creado_por=request.user
    ).select_related("creado_por")[:100]
    return render(request, "BancoPreguntas.html", {
        "formulario": formulario, "mias": mias, "pendientes": pendientes,
        "aprobadas": PreguntaBanco.objects.filter(
            estado="APROBADA", activo=True
        ).count(),
        "materias": PreguntaBanco.MATERIAS,
    })


@login_required
@require_http_methods(["GET", "POST"])
def editar_pregunta_banco(request, pregunta_id):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes acceso a la curaduría.")
    pregunta = get_object_or_404(PreguntaBanco, pk=pregunta_id)
    if pregunta.creado_por_id != request.user.pk:
        raise PermissionDenied("Solo puedes editar tus propios borradores.")
    if pregunta.estado not in ("BORRADOR", "RECHAZADA"):
        raise PermissionDenied("Las preguntas enviadas o aprobadas están bloqueadas.")

    formulario = PreguntaBancoForm(
        request.POST if request.method == "POST" else None, instance=pregunta,
    )
    if request.method == "POST" and formulario.is_valid():
        actualizada = formulario.save(commit=False)
        actualizada.estado = "BORRADOR"
        actualizada.observaciones_revision = ""
        actualizada.revisado_por = None
        actualizada.revisado_en = None
        try:
            with transaction.atomic():
                actualizada.save()
        except IntegrityError:
            formulario.add_error("enunciado", "Ya existe una pregunta idéntica.")
        else:
            messages.success(request, "Borrador actualizado; envíalo a revisión.")
            return redirect("banco_preguntas")
    return render(request, "EditarPreguntaBanco.html", {
        "formulario": formulario, "pregunta": pregunta,
    })


@login_required
@require_POST
def enviar_pregunta_revision(request, pregunta_id):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes permisos de curaduría.")
    with transaction.atomic():
        pregunta = get_object_or_404(
            PreguntaBanco.objects.select_for_update(), pk=pregunta_id,
        )
        if pregunta.creado_por_id != request.user.pk:
            raise PermissionDenied("No puedes enviar preguntas ajenas.")
        if pregunta.estado not in ("BORRADOR", "RECHAZADA"):
            raise PermissionDenied("Este registro ya fue enviado o aprobado.")
        pregunta.full_clean()
        pregunta.estado = "EN_REVISION"
        pregunta.revisado_por = None
        pregunta.revisado_en = None
        pregunta.observaciones_revision = ""
        pregunta.save(update_fields=(
            "estado", "revisado_por", "revisado_en", "observaciones_revision",
            "actualizado_en",
        ))
    messages.success(request, "Pregunta enviada a revisión docente.")
    return redirect("banco_preguntas")


@login_required
@require_http_methods(["GET", "POST"])
def revisar_pregunta_banco(request, pregunta_id):
    if not puede_curaduría(request.user):
        raise PermissionDenied("No tienes permiso para revisar preguntas.")

    pregunta = get_object_or_404(PreguntaBanco, pk=pregunta_id)
    if pregunta.creado_por_id == request.user.pk:
        raise PermissionDenied("Nadie puede aprobar una pregunta que creó.")
    if pregunta.estado != "EN_REVISION":
        raise PermissionDenied("Solo pueden revisarse preguntas pendientes.")

    if request.method == "POST":
        accion = request.POST.get("accion", "")
        observacion = request.POST.get("observacion", "").strip()
        if accion not in ("aprobar", "rechazar"):
            raise Http404("Acción inválida.")
        if len(observacion) > 1000 or (accion == "rechazar" and len(observacion) < 10):
            return render(request, "RevisarPreguntaBanco.html", {
                "pregunta": pregunta,
                "error": "Indica un motivo de rechazo de 10 a 1000 caracteres.",
            }, status=400)
        with transaction.atomic():
            actual = get_object_or_404(
                PreguntaBanco.objects.select_for_update(), pk=pregunta_id,
            )
            if actual.estado != "EN_REVISION" or actual.creado_por_id == request.user.pk:
                raise PermissionDenied("La pregunta cambió de estado o no tienes permiso.")
            if accion == "aprobar":
                actual.full_clean()
            actual.estado = "APROBADA" if accion == "aprobar" else "RECHAZADA"
            actual.observaciones_revision = observacion
            actual.revisado_por = request.user
            actual.revisado_en = timezone.now()
            actual.save(update_fields=(
                "estado", "observaciones_revision", "revisado_por",
                "revisado_en", "actualizado_en",
            ))
        messages.success(request, "Revisión guardada. Solo las aprobadas se publican.")
        return redirect("banco_preguntas")

    return render(request, "RevisarPreguntaBanco.html", {"pregunta": pregunta})
