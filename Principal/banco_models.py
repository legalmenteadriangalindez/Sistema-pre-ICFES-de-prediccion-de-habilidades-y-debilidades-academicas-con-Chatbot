"""Banco curado de preguntas, independiente de los simulacros históricos."""
import hashlib
import unicodedata

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class PreguntaBanco(models.Model):
    """Solo las preguntas aprobadas y activas se utilizan para practicar."""

    MATERIAS = (
        ("Matemáticas", "Matemáticas"),
        ("Lectura Crítica", "Lectura Crítica"),
        ("Sociales y Ciudadanas", "Sociales y Ciudadanas"),
        ("Ciencias Naturales", "Ciencias Naturales"),
        ("Inglés", "Inglés"),
    )
    DIFICULTADES = (("BASICA", "Básica"), ("MEDIA", "Media"), ("ALTA", "Alta"))
    ESTADOS = (
        ("BORRADOR", "Borrador"), ("EN_REVISION", "En revisión"),
        ("APROBADA", "Aprobada"), ("RECHAZADA", "Rechazada"),
    )
    ORIGENES = (("DOCENTE", "Docente"), ("IA", "Generada por IA"))

    materia = models.CharField(max_length=32, choices=MATERIAS)
    competencia = models.CharField(max_length=100)
    evidencia = models.CharField(max_length=200, blank=True)
    dificultad = models.CharField(max_length=8, choices=DIFICULTADES, default="MEDIA")
    contexto = models.TextField(blank=True)
    enunciado = models.TextField(max_length=2000)
    opciones = models.JSONField()
    respuesta_correcta = models.CharField(max_length=1)
    explicacion = models.TextField(max_length=2000)
    # Historial inmutable: cada nueva revisión es otra fila con identidad propia.
    revision_de = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="revisiones",
    )
    numero_version = models.PositiveIntegerField(default=1)
    huella = models.CharField(max_length=64, unique=True, editable=False)
    estado = models.CharField(max_length=12, choices=ESTADOS, default="BORRADOR")
    origen = models.CharField(max_length=8, choices=ORIGENES, default="DOCENTE")
    creado_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="preguntas_banco_creadas",
    )
    revisado_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="preguntas_banco_revisadas",
    )
    observaciones_revision = models.TextField(max_length=1000, blank=True)
    revisado_en = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-creado_en", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=["revision_de", "numero_version"],
                name="unique_version_por_pregunta_raiz",
            ),
        ]

    @staticmethod
    def generar_huella(materia, enunciado):
        def normalizar(texto):
            return " ".join(unicodedata.normalize("NFKC", str(texto)).casefold().split())

        return hashlib.sha256(
            (normalizar(materia) + "|" + normalizar(enunciado)).encode("utf-8")
        ).hexdigest()

    def clean(self):
        super().clean()
        opciones = self.opciones
        claves = ("A", "B", "C", "D")
        if not isinstance(opciones, dict) or set(opciones) != set(claves):
            raise ValidationError({"opciones": "Se necesitan exactamente cuatro opciones A, B, C y D."})
        if any(not isinstance(opciones[k], str) or not opciones[k].strip() for k in claves):
            raise ValidationError({"opciones": "Todas las opciones deben tener contenido."})
        valores = [" ".join(opciones[k].casefold().split()) for k in claves]
        if len(set(valores)) != 4:
            raise ValidationError({"opciones": "Las alternativas deben ser diferentes."})
        if self.respuesta_correcta not in claves:
            raise ValidationError({"respuesta_correcta": "La respuesta debe ser A, B, C o D."})
        if not self.competencia.strip() or not self.enunciado.strip() or not self.explicacion.strip():
            raise ValidationError("Competencia, pregunta y explicación son obligatorias.")
        huella = self.huella_para_version()
        if self.revision_de_id and (
            self.numero_version < 2
            or (self.revision_de and self.revision_de.revision_de_id is not None)
        ):
            raise ValidationError("La revisión debe apuntar a la primera versión.")
        if PreguntaBanco.objects.filter(huella=huella).exclude(pk=self.pk).exists():
            raise ValidationError({"enunciado": "Ya existe esta pregunta para la misma materia."})

    def huella_para_version(self):
        base = self.generar_huella(self.materia, self.enunciado)
        if self.revision_de_id:
            return hashlib.sha256(
                f"{base}|raiz={self.revision_de_id}|v={self.numero_version}".encode("utf-8")
            ).hexdigest()
        return base

    def save(self, *args, **kwargs):
        self.huella = self.huella_para_version()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"huella"}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.materia}: {self.enunciado[:70]}"
