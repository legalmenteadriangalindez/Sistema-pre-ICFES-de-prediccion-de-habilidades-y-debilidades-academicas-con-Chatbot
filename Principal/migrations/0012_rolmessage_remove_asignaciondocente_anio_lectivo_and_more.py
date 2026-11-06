"""Sincroniza los modelos actuales con el historial 0001–0011.

Las restricciones se eliminan ANTES de quitar campos referenciados por ellas:
en SQLite, invertir ese orden rompe la reconstrucción de tablas.

Esta migración corresponde a la base limpia de desarrollo de Pre-ICFES.
Antes de aplicarla a una base con datos reales, se debe planear la migración
de los registros afectados por campos y modelos eliminados.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Principal", "0011_evaluaciones_fase1"),
    ]

    operations = [
        # Primero retirar todas las restricciones que usan campos antiguos.
        migrations.RemoveConstraint(
            model_name="asignaciondocente", name="unique_asignacion_docente"
        ),
        migrations.RemoveConstraint(
            model_name="periodoacademico", name="unique_periodo_por_anio"
        ),
        migrations.RemoveConstraint(
            model_name="boletin", name="unique_boletin_matricula_periodo"
        ),
        migrations.RemoveConstraint(
            model_name="curso", name="unique_curso_grado_nombre_jornada"
        ),
        migrations.RemoveConstraint(
            model_name="nota", name="unique_nota_matricula_asignacion_periodo"
        ),
        migrations.RemoveConstraint(
            model_name="observacion", name="unique_observacion_matricula_asignacion_periodo"
        ),
        migrations.RemoveConstraint(
            model_name="temaasignado", name="unique_tema_asignado"
        ),
        migrations.CreateModel(
            name="RolMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=10)),
                ("descripcion", models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(model_name="asignaciondocente", name="anio_lectivo"),
        migrations.RemoveField(model_name="asignaciondocente", name="curso"),
        migrations.RemoveField(model_name="asignaciondocente", name="docente"),
        migrations.RemoveField(model_name="asignaciondocente", name="materia"),
        migrations.RemoveField(model_name="asignaciondocente", name="sede"),
        migrations.RemoveField(model_name="nota", name="asignacion"),
        migrations.RemoveField(model_name="observacion", name="asignacion"),
        migrations.RemoveField(model_name="docente", name="persona"),
        migrations.RemoveField(model_name="curso", name="jornada"),
        migrations.RemoveField(model_name="periodoacademico", name="anio_lectivo"),
        migrations.RemoveField(model_name="observacion", name="periodo"),
        migrations.RemoveField(model_name="boletin", name="periodo"),
        migrations.RemoveField(model_name="temaasignado", name="periodo"),
        migrations.RemoveField(model_name="nota", name="periodo"),
        migrations.RemoveField(model_name="preferenciaaccesibilidad", name="estudiante"),
        migrations.AddField(
            model_name="preferenciaaccesibilidad",
            name="perfil",
            field=models.OneToOneField(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="Principal.perfilusuario",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="boletin",
            constraint=models.UniqueConstraint(
                fields=("matricula",), name="unique_boletin_matricula"
            ),
        ),
        migrations.AddConstraint(
            model_name="curso",
            constraint=models.UniqueConstraint(
                fields=("grado", "nombre"), name="unique_curso_grado_nombre"
            ),
        ),
        migrations.AddConstraint(
            model_name="nota",
            constraint=models.UniqueConstraint(
                fields=("matricula",), name="unique_nota_matricula"
            ),
        ),
        migrations.AddConstraint(
            model_name="observacion",
            constraint=models.UniqueConstraint(
                fields=("matricula",), name="unique_observacion_matricula"
            ),
        ),
        migrations.AddConstraint(
            model_name="temaasignado",
            constraint=models.UniqueConstraint(
                fields=("estudiante", "tema"), name="unique_tema"
            ),
        ),
        migrations.AlterField(
            model_name="mensaje",
            name="rol",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="Principal.rolmessage",
            ),
        ),
        migrations.DeleteModel(name="Sede"),
        migrations.DeleteModel(name="AsignacionDocente"),
        migrations.DeleteModel(name="Docente"),
        migrations.DeleteModel(name="Jornada"),
        migrations.DeleteModel(name="PeriodoAcademico"),
    ]
