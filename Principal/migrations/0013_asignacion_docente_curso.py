"""Agrega asignaciones docentes explícitas sin cambiar datos académicos existentes."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0012_rolmessage_remove_asignaciondocente_anio_lectivo_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AsignacionDocenteCurso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activo", models.BooleanField(default=True)),
                ("anio_lectivo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="docentes_asignados", to="Principal.aniolectivo")),
                ("curso", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="docentes_asignados", to="Principal.curso")),
                ("docente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cursos_asignados", to="Principal.perfilusuario")),
            ],
        ),
        migrations.AddConstraint(
            model_name="asignaciondocentecurso",
            constraint=models.UniqueConstraint(
                fields=("docente", "curso", "anio_lectivo"),
                name="unique_docente_curso_anio",
            ),
        ),
    ]
