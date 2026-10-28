from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("Principal", "0010_remove_persona_user_persona_perfil_user")]

    operations = [
        migrations.CreateModel(
            name="IntentoEvaluacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("materia", models.CharField(max_length=100)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("total_preguntas", models.PositiveIntegerField()),
                ("aciertos", models.PositiveIntegerField()),
                ("estudiante", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="intentos_evaluacion", to="Principal.estudiante")),
            ],
        ),
        migrations.CreateModel(
            name="RespuestaEvaluacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero", models.PositiveIntegerField()),
                ("competencia", models.CharField(max_length=100)),
                ("enunciado", models.TextField()),
                ("pregunta", models.TextField()),
                ("opciones", models.JSONField()),
                ("respuesta_estudiante", models.CharField(blank=True, max_length=1)),
                ("respuesta_correcta", models.CharField(max_length=1)),
                ("explicacion", models.TextField()),
                ("es_correcta", models.BooleanField()),
                ("intento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="respuestas", to="Principal.intentoevaluacion")),
            ],
        ),
        migrations.AddConstraint(model_name="respuest a evaluacion".replace(" ", ""), constraint=models.UniqueConstraint(fields=("intento", "numero"), name="unique_respuesta_intento_numero")),
    ]
