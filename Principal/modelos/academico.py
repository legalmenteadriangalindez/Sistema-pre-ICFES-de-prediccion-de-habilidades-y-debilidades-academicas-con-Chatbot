"""Modelos de matrícula, personas académicas y seguimiento escolar."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .identidad import Acudiente, PerfilUsuario, Persona, RelacionAcudiente


class Grado(models.Model):
    codigo = models.CharField(max_length=10,unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"GRD-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return f" {self.nombre} ({self.codigo}°)"
#******************TABLA GRADO******************




# ==================TABLA CURSO=================


class Curso(models.Model):
    grado = models.ForeignKey(Grado, on_delete=models.PROTECT,related_name="cursos")
    nombre = models.CharField(max_length=20)
    cupo_maximo = models.PositiveIntegerField(default=30)
    activo = models.BooleanField(default=True)
    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["grado", "nombre"],
            name="unique_curso_grado_nombre"
        )
    ]

    def __str__(self):
        return f"{self.grado.codigo}° {self.nombre}"
#*******************TABLA CURSO*****************




# ================== TABLA AÑO LECTIVO ==================


class AnioLectivo(models.Model):
    anio = models.PositiveIntegerField(unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)

    def __str__(self):
        return str(self.anio)
# ****************** TABLA AÑO LECTIVO ******************



# ================== TABLA MATERIA ==================


class Materia(models.Model):
    codigo = models.CharField(max_length=10, unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"MAT-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre
# ****************** TABLA MATERIA ******************





#==================TABLA ESTUDIANTE=============


class Estudiante(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE)
    necesidades_especiales = models.TextField(blank=True,null=True)


    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"
#*********************TABLA ESTUDIANTE******************




#====================TABLA ESTUDIANTE ACUDIENTE============


class EstudianteAcudiente(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    acudiente = models.ForeignKey(Acudiente, on_delete=models.CASCADE)
    relacion = models.ForeignKey(RelacionAcudiente, on_delete=models.PROTECT)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante","acudiente"],
                name="unique_estudiante_acudiente"
            )
        ]
#*********************TABLA ESTUDIANTE ACUDIENTE************




#============TABLA MATRICULA================


class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    anio_lectivo = models.ForeignKey(AnioLectivo, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante","anio_lectivo"],
                name="unique_matricula_anual"
            )
        ]

#************TABLA MATRICULA***************




# ================== TABLA NOTA ==================


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, null=True, blank=True)
    valor = models.DecimalField(max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matricula"],
                name="unique_nota_matricula"
            )
        ]

    def __str__(self):
        if self.matricula:
            return f"{self.matricula.estudiante} - {self.valor}"
        return f"Nota {self.valor}"
# Vinculación explícita de docentes con cursos por año lectivo.
# Se utiliza tanto para filtrar las pantallas como para autorizar cada POST.


class AsignacionDocenteCurso(models.Model):
    docente = models.ForeignKey(
        PerfilUsuario, on_delete=models.CASCADE, related_name="cursos_asignados"
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, related_name="docentes_asignados"
    )
    anio_lectivo = models.ForeignKey(
        AnioLectivo, on_delete=models.CASCADE, related_name="docentes_asignados"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["docente", "curso", "anio_lectivo"],
                name="unique_docente_curso_anio",
            )
        ]

    def __str__(self):
        return f"{self.docente.user.username}: {self.curso} ({self.anio_lectivo})"


# ****************** TABLA NOTA ******************




# ================== TABLA BOLETÍN ==================


class Boletin(models.Model):
    matricula = models.ForeignKey(Matricula,on_delete=models.CASCADE,related_name="boletines", null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matricula"],
                name="unique_boletin_matricula"
            )
        ]

    def __str__(self):
        if self.matricula:
            return f"Boletín {self.matricula.estudiante}"
        return "Boletín sin matrícula"

# ****************** TABLA BOLETÍN ******************




# ================== TABLA OBSERVACIÓN ==================


class Observacion(models.Model):
    matricula = models.ForeignKey(Matricula,on_delete=models.CASCADE,related_name="observaciones", null=True, blank=True)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matricula"],
                name="unique_observacion_matricula"
            )
        ]
    def __str__(self):
        if self.matricula:
            return f"Observación {self.matricula.estudiante}"
        return "Observación sin matrícula"

# ****************** TABLA OBSERVACIÓN ******************




#==================TABLA RITMOS DE APRENDIZAJE=====