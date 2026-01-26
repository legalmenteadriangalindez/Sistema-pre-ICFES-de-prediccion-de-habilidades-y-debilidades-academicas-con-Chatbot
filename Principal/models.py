from django.db import models

from django.contrib.auth.models import User

from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  # ADMIN, ESTUDIANTE, DOCENTE, ACUDIENTE
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.ManyToManyField(Rol, related_name="usuarios")  # un usuario puede tener varios roles

    def __str__(self):
        return self.user.username


#===================TABLA SEXO====================
class Sexo(models.Model):
    codigo = models.CharField(max_length=50,unique=True,editable=False,blank=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)
     
    def save(self,*args,**kwargs):
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"SEX-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
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
    codigo = models.CharField(max_length=15,unique=True,editable=False,blank=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"REL-ACU-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
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



# ==================TABLA JORNADA=================
class Jornada(models.Model):
    codigo = models.CharField(max_length=10,unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    
    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"JND-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre
#*******************TABLA JORNADA*****************



# ==================TABLA CURSO=================
class Curso(models.Model):
    grado = models.ForeignKey(Grado, on_delete=models.PROTECT,related_name="cursos")
    nombre = models.CharField(max_length=20)
    jornada = models.ForeignKey(Jornada, on_delete=models.PROTECT,related_name="cursos")
    cupo_maximo = models.PositiveIntegerField(default=30)
    activo = models.BooleanField(default=True)
    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["grado", "nombre", "jornada"],
            name="unique_curso_grado_nombre_jornada"
        )
    ]

    def __str__(self):
        return f"{self.grado.codigo}° {self.nombre} - {self.jornada.nombre}"
#*******************TABLA CURSO*****************



# ================== TABLA SEDE ==================
class Sede(models.Model):
    codigo = models.CharField(max_length=10, unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"SED-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
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



# ================== TABLA ASIGNACIÓN DOCENTE ==================
class AsignacionDocente(models.Model):
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    anio_lectivo = models.ForeignKey(AnioLectivo, on_delete=models.PROTECT)
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    
    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["docente", "curso", "materia", "anio_lectivo", "sede"],
            name="unique_asignacion_docente"
        )
    ]

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
        constraints = [
        models.UniqueConstraint(
            fields=["numero", "anio_lectivo"],
            name="unique_periodo_por_anio"
        )
    ]

    def __str__(self):
        return f"{self.nombre} - {self.anio_lectivo.anio}"
# ****************** TABLA PERIODO ACADÉMICO ******************



#==================TABLA ESTUDIANTE=============
class Estudiante(models.Model):
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    necesidades_especiales = models.TextField(blank=True,null=True)

    acudiente = models.ForeignKey(Acudiente,related_name="estudiantes",on_delete=models.SET_NULL,null=True,blank=True,)

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"
#*********************TABLA ESTUDIANTE******************



# ================== TABLA NOTA ==================
class Nota(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente,on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)

    valor = models.DecimalField(max_digits=4, decimal_places=2,validators=[MinValueValidator(0), MaxValueValidator(5)])  # 0.00 a 5.00
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "asignacion", "periodo"],
            name="unique_nota_estudiante_asignacion_periodo"
        )
    ]

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
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "periodo"],
            name="unique_boletin_estudiante_periodo"
        )
    ]

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
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "asignacion", "periodo"],
            name="unique_observacion_est_asig_periodo"
        )
    ]

    def __str__(self):
        return f"Obs {self.estudiante} - {self.asignacion.materia}"
# ****************** TABLA OBSERVACIÓN ******************


#==================TABLA RITMOS DE APRENDIZAJE=====
class RitmoAprendizaje(models.Model):
    codigo = models.CharField(max_length=10, unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=50)  # Lento, Medio, Rápido
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"RIT-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre
#****************TABLA RITMOS DE APRENDIZAJE*******



#==================TABLA ESTILOs DE APRENDIZAJE=====
class EstiloAprendizaje(models.Model):
    codigo = models.CharField(max_length=10, unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=50)  # Visual, Auditivo, Kinestésico
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"EST-{(str(self.id).zfill(3))}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre
#****************TABLA ESTILOS DE APRENDIZAJE*******



#==================TABLA NIVEL DE APREDIZAJE=====
class NivelAprendizaje(models.Model):
    codigo = models.CharField(max_length=10, unique=True,editable=False,blank=True)
    nombre = models.CharField(max_length=50)  # Bajo, Básico, Alto, Superior
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
       
        if not self.pk:
            super().save(*args,**kwargs)
            self.codigo = f"NIV-{str(self.id).zfill(3)}"
            super().save(update_fields=["codigo"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre
#*******************TABLA NIVEL DE APREDIZAJE****


#===================TABLA PERFIL PEDAGOGICO========
class PerfilPedagogico(models.Model):
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE)
    ritmo = models.ForeignKey(RitmoAprendizaje, on_delete=models.PROTECT)
    estilo = models.ForeignKey(EstiloAprendizaje, on_delete=models.PROTECT)
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil {self.estudiante}"
#*******************TABLA PERFIL PEDAGOGICO********




#==========TABLA  RIESGOS=========================
class Riesgo(models.Model):
    nombre = models.CharField(max_length=50)  
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
#**********TABLA RIESGOS**************************


#==========TABLA PREDICCION DE RIESGO===========
class PrediccionRiesgo(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    riesgo = models.ForeignKey(Riesgo, on_delete=models.PROTECT)
    probabilidad = models.DecimalField(max_digits=5, decimal_places=2,validators=[MinValueValidator(0), MaxValueValidator(1)])
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "riesgo"],
            name="unique_prediccion_riesgo"
        )
    ]

    def __str__(self):
        return f"{self.estudiante} - {self.riesgo}"
#**********TABLA PREDICCION DE RIESGO***********



#==========TABLA RECOMENDACIONES================
class Recomendacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rec {self.estudiante}"
#**********TABLA RECOMENDACIONES****************



#=====TABLA PREFERNCIAS DE ACCECIBILIDAD=======
class PreferenciaAccesibilidad(models.Model):
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE)
    necesita_audio = models.BooleanField(default=False)
    necesita_visual = models.BooleanField(default=False)
    necesita_texto_simple = models.BooleanField(default=False)

    def __str__(self):
        return f"Accesibilidad {self.estudiante}"
#*****TABLA PREFERNCIAS DE ACCECIBILIDAD*******


#==================TABLA TEMAS===============
class Tema(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True,null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["materia", "nombre"],
            name="unique_tema_por_materia"
        )
    ]

    def __str__(self):
        return self.nombre
#******************TABLA TEMAS***************


#===============TABLA TEMAS ASIGNADOS===========
class TemaAsignado(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "tema", "periodo"],
            name="unique_tema_asignado"
        )
    ]

    def __str__(self):
        return f"{self.estudiante} - {self.tema}"
#***************TABLA TEMAS ASIGNADOS***********


#==========TABLA PROGRESO DEL TEMA ASIGNADO========
class ProgresoTema(models.Model):
    tema_asignado = models.OneToOneField(TemaAsignado, on_delete=models.CASCADE)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tema_asignado} {self.porcentaje}%"
#**********TABLA PROGRESO DEL TEMA ASIGNADO********



#==========TABLA ACTIVIDADES========
class Actividad(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo
#**********TABLA ACTIVIDADES********



#==========TABLA ACTIVIDADES ASIGNADAS========
class ActividadAsignada(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.PROTECT)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "actividad"],
            name="unique_actividad_asignada"
        )
    ]

    def __str__(self):
        return f"{self.estudiante} - {self.actividad}"
#**********TABLA ACTIVIDADES ASIGNADAS********



#===========TABLA DE ANALISIS COGNITIVO======
class AnalisisCognitivo(models.Model):
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE)
    nivel_general = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    dudas_frecuentes = models.TextField()
    areas_fuertes = models.TextField()
    areas_debiles = models.TextField()
    fecha = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Análisis {self.estudiante}"
#***********TABLA DE ANALISIS COGNITIVO*****



#===========TABLA CARRERAS==============
class Carrera(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
#***********TABLA CARRERAS**************



#==========TABLA RECOMENDACION VOCACIONAL======
class RecomendacionVocacional(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    compatibilidad = models.DecimalField(max_digits=5, decimal_places=2)
    conocimientos_necesarios = models.TextField()
    puntaje_requerido = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.estudiante} - {self.carrera}"
#**********TABLA RECOMENDACION VOCACIONAL*******



#===========TABLA MATERIALES ===============
class MaterialEstudio(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=100)
    url = models.URLField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo
#*************TABLA MATERIALES*****************



#==========TABLA MATERIALES ASIGNADOS=======
class MaterialAsignado(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    material = models.ForeignKey(MaterialEstudio, on_delete=models.PROTECT)
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
#**********TABLA MATERIALES ASIGNADOS*******