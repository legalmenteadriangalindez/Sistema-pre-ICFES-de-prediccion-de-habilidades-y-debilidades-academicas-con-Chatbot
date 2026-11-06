"""Planes y sesiones semanales guardados en la base de datos.

Se genera una instantánea por estudiante y semana; el sistema no sobrescribe
sesiones completadas ni planes históricos cuando llegan nuevas evaluaciones.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0013_asignacion_docente_curso"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlanEstudioSemanal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("semana_inicio", models.DateField()),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("con_datos_academicos", models.BooleanField(default=False)),
                ("estudiante", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="planes_semanales", to="Principal.estudiante",
                )),
            ],
            options={"ordering": ["-semana_inicio"]},
        ),
        migrations.CreateModel(
            name="SesionPlanSemanal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dia_indice", models.PositiveSmallIntegerField()),
                ("dia_nombre", models.CharField(max_length=12)),
                ("fecha_programada", models.DateField()),
                ("area", models.CharField(max_length=100)),
                ("actividad", models.CharField(max_length=250)),
                ("minutos_previstos", models.PositiveSmallIntegerField()),
                ("destino", models.CharField(default="test", max_length=32)),
                ("completada", models.BooleanField(default=False)),
                ("minutos_realizados", models.PositiveSmallIntegerField(default=0)),
                ("fecha_completada", models.DateTimeField(blank=True, null=True)),
                ("notas", models.CharField(blank=True, max_length=500)),
                ("plan", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sesiones", to="Principal.planestudiosemanal",
                )),
            ],
            options={"ordering": ["dia_indice"]},
        ),
        migrations.AddConstraint(
            model_name="planestudiosemanal",
            constraint=models.UniqueConstraint(
                fields=("estudiante", "semana_inicio"),
                name="uq_plan_estudiante_semana",
            ),
        ),
        migrations.AddConstraint(
            model_name="sesionplansemanal",
            constraint=models.UniqueConstraint(
                fields=("plan", "dia_indice"),
                name="uq_sesion_plan_dia",
            ),
        ),
    ]
