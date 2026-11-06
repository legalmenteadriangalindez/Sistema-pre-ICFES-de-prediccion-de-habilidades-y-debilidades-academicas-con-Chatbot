# Generated manually from the additive DocenteCurso model; no existing tables are altered.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('Principal', '0012_rolmessage_remove_asignaciondocente_anio_lectivo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocenteCurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='docentes_asignados', to='Principal.curso')),
                ('docente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cursos_docentes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='docentecurso',
            constraint=models.UniqueConstraint(fields=('docente', 'curso'), name='unique_docente_curso_actual'),
        ),
    ]
