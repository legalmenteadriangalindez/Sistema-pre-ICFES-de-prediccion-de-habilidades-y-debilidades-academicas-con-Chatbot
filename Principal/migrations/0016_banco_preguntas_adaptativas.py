"""Crear el banco curado y enlazar respuestas históricas de forma opcional."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0015_docente_autoria_retroalimentacion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PreguntaBanco",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("materia", models.CharField(choices=[
                    ("Matemáticas", "Matemáticas"),
                    ("Lectura Crítica", "Lectura Crítica"),
                    ("Sociales y Ciudadanas", "Sociales y Ciudadanas"),
                    ("Ciencias Naturales", "Ciencias Naturales"),
                    ("Inglés", "Inglés"),
                ], max_length=32)),
                ("competencia", models.CharField(max_length=100)),
                ("dificultad", models.CharField(choices=[
                    ("BASICA", "Básica"), ("MEDIA", "Media"), ("ALTA", "Alta"),
                ], default="MEDIA", max_length=8)),
                ("contexto", models.TextField(blank=True)),
                ("enunciado", models.TextField(max_length=2000)),
                ("opciones", models.JSONField()),
                ("respuesta_correcta", models.CharField(max_length=1)),
                ("explicacion", models.TextField(max_length=2000)),
                ("huella", models.CharField(editable=False, max_length=64, unique=True)),
                ("estado", models.CharField(choices=[
                    ("BORRADOR", "Borrador"), ("EN_REVISION", "En revisión"),
                    ("APROBADA", "Aprobada"), ("RECHAZADA", "Rechazada"),
                ], default="BORRADOR", max_length=12)),
                ("origen", models.CharField(choices=[
                    ("DOCENTE", "Docente"), ("IA", "Generada por IA"),
                ], default="DOCENTE", max_length=8)),
                ("observaciones_revision", models.TextField(blank=True, max_length=1000)),
                ("revisado_en", models.DateTimeField(blank=True, null=True)),
                ("activo", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("creado_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="preguntas_banco_creadas", to=settings.AUTH_USER_MODEL,
                )),
                ("revisado_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="preguntas_banco_revisadas", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ("-creado_en", "-pk")},
        ),
        migrations.AddField(
            model_name="respuestaevaluacion",
            name="pregunta_banco",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="respuestas_evaluacion", to="Principal.preguntabanco",
            ),
        ),
    ]
