"""Nuevas tablas sin alterar evaluaciones, matrículas o usuarios anteriores."""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0017_simulacro_versionado_intervencion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="RepasoEspaciado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("aciertos_seguidos", models.PositiveSmallIntegerField(default=0)),
                ("intervalo_dias", models.PositiveIntegerField(default=1)),
                ("proximo_repaso", models.DateField(default=django.utils.timezone.localdate)),
                ("ultima_respuesta", models.DateTimeField(blank=True, null=True)),
                ("estudiante", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="repasos_espaciados", to="Principal.estudiante")),
                ("pregunta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="programaciones_repaso", to="Principal.preguntabanco")),
            ],
            options={"ordering": ("proximo_repaso", "pk")},
        ),
        migrations.AddConstraint(
            model_name="repasoespaciado",
            constraint=models.UniqueConstraint(fields=("estudiante", "pregunta"), name="unique_repaso_estudiante_pregunta"),
        ),
        migrations.CreateModel(
            name="NotificacionAcademica",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("categoria", models.CharField(max_length=32)),
                ("titulo", models.CharField(max_length=140)),
                ("mensaje", models.CharField(max_length=500)),
                ("clave", models.CharField(max_length=100)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("leida_en", models.DateTimeField(blank=True, null=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="avisos_academicos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-fecha", "-pk")},
        ),
        migrations.AddConstraint(
            model_name="notificacionacademica",
            constraint=models.UniqueConstraint(fields=("usuario", "clave"), name="unique_aviso_por_usuario"),
        ),
        migrations.CreateModel(
            name="PreferenciaAvisos",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recibir_avisos", models.BooleanField(default=True)),
                ("avisos_familiares", models.BooleanField(default=False)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="preferencias_avisos", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="RegistroAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("accion", models.CharField(max_length=64)),
                ("recurso", models.CharField(max_length=60)),
                ("recurso_id", models.PositiveIntegerField(blank=True, null=True)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="auditoria_operaciones", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-fecha", "-pk")},
        ),
        migrations.CreateModel(
            name="ConsentimientoTutorIA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("autorizado", models.BooleanField(default=False)),
                ("registrado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("acudiente_usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consentimientos_tutor_ia", to=settings.AUTH_USER_MODEL)),
                ("estudiante", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="consentimiento_tutor_ia", to="Principal.estudiante")),
            ],
        ),
    ]
