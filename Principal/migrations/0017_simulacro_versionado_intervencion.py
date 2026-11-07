"""Versiones inmutables, simulacro persistente e intervención docente."""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0016_banco_preguntas_adaptativas"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="preguntabanco", name="numero_version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="preguntabanco", name="revision_de",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="revisiones", to="Principal.preguntabanco",
            ),
        ),
        migrations.AddConstraint(
            model_name="preguntabanco",
            constraint=models.UniqueConstraint(
                fields=("revision_de", "numero_version"),
                name="unique_version_por_pregunta_raiz",
            ),
        ),
        migrations.CreateModel(
            name="SimulacroAvanzado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado", models.CharField(
                    max_length=12, default="EN_CURSO",
                    choices=[("EN_CURSO", "En curso"), ("PAUSADO", "En pausa"), ("FINALIZADO", "Finalizado")],
                )),
                ("bloque", models.PositiveSmallIntegerField(default=1)),
                ("preguntas", models.JSONField(default=list)),
                ("respuestas", models.JSONField(default=dict)),
                ("restantes_segundos", models.PositiveIntegerField(default=4500)),
                ("vence_en", models.DateTimeField()),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("finalizado_en", models.DateTimeField(blank=True, null=True)),
                ("estudiante", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="simulacros_avanzados", to="Principal.estudiante",
                )),
                ("intento", models.OneToOneField(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="simulacro_avanzado", to="Principal.intentoevaluacion",
                )),
            ],
            options={"ordering": ("-creado_en", "-pk")},
        ),
        migrations.AddConstraint(
            model_name="simulacroavanzado",
            constraint=models.UniqueConstraint(
                fields=("estudiante",),
                condition=models.Q(estado__in=["EN_CURSO", "PAUSADO"]),
                name="unique_simu_avanzado_activo_estudiante",
            ),
        ),
        migrations.CreateModel(
            name="IntervencionAcademica",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("materia", models.CharField(max_length=32, choices=[
                    ("Matemáticas", "Matemáticas"), ("Lectura Crítica", "Lectura Crítica"),
                    ("Sociales y Ciudadanas", "Sociales y Ciudadanas"),
                    ("Ciencias Naturales", "Ciencias Naturales"), ("Inglés", "Inglés"),
                ])),
                ("competencia", models.CharField(max_length=100)),
                ("objetivo", models.CharField(max_length=250)),
                ("actividades", models.TextField(max_length=2000)),
                ("fecha_revision", models.DateField()),
                ("estado", models.CharField(
                    default="ACTIVA", max_length=8,
                    choices=[("ACTIVA", "Activa"), ("CERRADA", "Cerrada")],
                )),
                ("observacion_cierre", models.TextField(blank=True, max_length=2000)),
                ("creado_en", models.DateTimeField(default=django.utils.timezone.now)),
                ("cerrado_en", models.DateTimeField(blank=True, null=True)),
                ("aciertos_inicial", models.PositiveIntegerField(default=0)),
                ("total_inicial", models.PositiveIntegerField(default=0)),
                ("aciertos_final", models.PositiveIntegerField(blank=True, null=True)),
                ("total_final", models.PositiveIntegerField(blank=True, null=True)),
                ("docente", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="intervenciones_asignadas", to=settings.AUTH_USER_MODEL,
                )),
                ("matricula", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="intervenciones_academicas", to="Principal.matricula",
                )),
            ],
            options={"ordering": ("-creado_en", "-pk")},
        ),
    ]
