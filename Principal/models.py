from django.db import models

from django.contrib.auth.models import User

# Create your models here.

#===================TABLA SEXO=====================
class Sexo(models.Model):
    codigo = models.CharField(max_length=50,unique=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.descripcion
#*******************TABLA SEXO*********************



#====================TABLA PERSONA==============================
class Persona(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    sexo = models.ForeignKey(Sexo, on_delete=models.PROTECT)
    def __str__(self):
       return f"{self.nombre} {self.apellido}"
#********************TABLA PERSONA******************************



#====================TABLA RELACION ACUDIENTE======
class RelacionAcudiente(models.Model):
    codigo = models.CharField(max_length=10,unique=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.descripcion
#********************TABLA RELACION ACUDIENTE***********************



#==================TABLA ACUDIENTE=============
class Acudiente(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE)
    relacion = models.ForeignKey(RelacionAcudiente, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"
#********************TABLA ACUDIENTE********************



#==================TABLA DOCENTE=============
class Docente(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.persona)
#*****************TABLA DOCENTE*******************



#==================TABLA GRADO==================

class Grado(models.Model):
    codigo = models.CharField(max_length=10,unique=True)
    nombre = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f" {self.nombre} ({self.codigo}°)"
#******************TABLA GRADO******************



# ==================TABLA JORNADA=================
class Jornada(models.Model):
    codigo = models.CharField(max_length=10,unique=True)
    nombre = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
#*******************TABLA JORNADA*****************



# ==================TABLA CURSO=================
class Curso(models.Model):
    grado = models.ForeignKey(Grado, on_delete=models.PROTECT,related_name="cursos")
    nombre = models.CharField(max_length=20)
    jornada = models.ForeignKey(Jornada, on_delete=models.PROTECT,related_name="cursos")
    cupo_maximo = models.PositiveBigIntegerField(default=30)
    activo = models.BooleanField(default=True)
    class Meta:
        unique_together = ("grado","nombre","jornada")

    def __str__(self):
        return f"{self.grado.codigo}° {self.nombre} - {self.jornada.nombre}"
#*******************TABLA CURSO*****************



# ================== TABLA SEDE ==================
class Sede(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
# ****************** TABLA SEDE ******************


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
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
# ****************** TABLA MATERIA ******************



# ================== TABLA ASIGNACIÓN DOCENTE ==================
class AsignacionDocente(models.Model):
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    anio_lectivo = models.ForeignKey(AnioLectivo, on_delete=models.PROTECT)
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = (
            "docente",
            "curso",
            "materia",
            "anio_lectivo",
            "sede"
        )

    def __str__(self):
        return f"{self.docente} - {self.materia} - {self.curso}"
# ****************** TABLA ASIGNACIÓN DOCENTE ******************



# ================== TABLA PERIODO ACADÉMICO ==================
class PeriodoAcademico(models.Model):
    numero = models.PositiveSmallIntegerField()  # 1, 2, 3, 4
    nombre = models.CharField(max_length=50)     # Primer Periodo
    anio_lectivo = models.ForeignKey(AnioLectivo, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)

    class Meta:
        unique_together = ("numero", "anio_lectivo")

    def __str__(self):
        return f"{self.nombre} - {self.anio_lectivo.anio}"
# ****************** TABLA PERIODO ACADÉMICO ******************



#==================TABLA ESTUDIANTE=============
class Estudiante(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
 
    necesidades_especiales = models.TextField(blank=True,null=True)

    acudiente = models.ForeignKey(Acudiente,on_delete=models.CASCADE,related_name="estudiantes")

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"
#*********************TABLA ESTUDIANTE******************



# ================== TABLA NOTA ==================
class Nota(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente,on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)

    valor = models.DecimalField(max_digits=4, decimal_places=2)  # 0.00 a 5.00
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "estudiante",
            "asignacion",
            "periodo"
        )

    def __str__(self):
        return f"{self.estudiante} - {self.valor}"
# ****************** TABLA NOTA ******************



# ================== TABLA BOLETÍN ==================
class Boletin(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    promedio_periodo = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True
    )
    observaciones_generales = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("estudiante", "periodo")

    def __str__(self):
        return f"Boletín {self.estudiante} - P{self.periodo.numero}"
# ****************** TABLA BOLETÍN ******************



# ================== TABLA OBSERVACIÓN ==================
class Observacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)

    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "estudiante",
            "asignacion",
            "periodo"
        )

    def __str__(self):
        return f"Obs {self.estudiante} - {self.asignacion.materia}"
# ****************** TABLA OBSERVACIÓN ******************
