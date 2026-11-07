"""Atribución docente y retroalimentación formativa; preserva datos antiguos."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0014_plan_estudio_semanal_persistente"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="actividad",
            name="creado_por",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="actividades_creadas", to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="actividadasignada",
            name="asignada_por",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="actividades_asignadas", to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="RetroalimentacionDocente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField(max_length=1000)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("docente", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="retroalimentaciones_emitidas", to=settings.AUTH_USER_MODEL,
                )),
                ("matricula", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="retroalimentaciones_docentes", to="Principal.matricula",
                )),
            ],
            options={"ordering": ["-creado_en", "-pk"]},
        ),
    ]
