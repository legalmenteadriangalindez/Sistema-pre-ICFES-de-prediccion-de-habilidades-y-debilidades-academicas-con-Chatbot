"""Modelos de aprendizaje, actividades y apoyos pedagógicos."""

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .academico import Estudiante, Materia, Matricula
from .identidad import PerfilUsuario


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
    nombre = models.CharField(max_length=50)  #Básico, Alto, Superior
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
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    ritmo = models.ForeignKey(RitmoAprendizaje, on_delete=models.PROTECT)
    estilo = models.ForeignKey(EstiloAprendizaje, on_delete=models.PROTECT)
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante"],
                name="unique_perfil_fecha"
            )
        ]
    def __str__(self):
        return f"Perfil {self.estudiante}"
#*******************TABLA PERFIL PEDAGOGICO********



#===========TABLA DE ANALISIS COGNITIVO======


class AnalisisCognitivo(models.Model):
    estudiante = models.ForeignKey(Estudiante,on_delete=models.CASCADE,related_name="analisis_cognitivos")    
    nivel_general = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    dudas_frecuentes = models.TextField()
    areas_fuertes = models.TextField()
    areas_debiles = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Análisis {self.estudiante}"
#***********TABLA DE ANALISIS COGNITIVO*****



#==========TABLA  RIESGOS=========================


class Riesgo(models.Model):
    nombre = models.CharField(max_length=50)  
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
#**********TABLA RIESGOS**************************



#==========TABLA PREDICCION DE RIESGO===========


class PrediccionRiesgo(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, null=True, blank=True)
    riesgo = models.ForeignKey(Riesgo, on_delete=models.PROTECT)
    probabilidad = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    validators=[MinValueValidator(0), MaxValueValidator(1)]
)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matricula", "riesgo"],
                name="unique_prediccion_riesgo"
            )
        ]
#**********TABLA PREDICCION DE RIESGO***********



#==========TABLA RECOMENDACIONES================


class Recomendacion(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, null=True, blank=True)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.matricula:
            return f"Recomendación {self.matricula.estudiante}"
        return "Recomendación sin matrícula"

#**********TABLA RECOMENDACIONES****************



#=====TABLA PREFERNCIAS DE ACCECIBILIDAD=======


class PreferenciaAccesibilidad(models.Model):
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE)
    necesita_audio = models.BooleanField(default=False)
    necesita_visual = models.BooleanField(default=False)
    necesita_texto_simple = models.BooleanField(default=False)

    def __str__(self):
        return f"Accesibilidad {self.perfil.user.username}"
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
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE) # 
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["estudiante", "tema"],
            name="unique_tema"
        )
    ]

    def __str__(self):
        return f"{self.estudiante} - {self.tema}"
#***************TABLA TEMAS ASIGNADOS***********



#==========TABLA PROGRESO DEL TEMA ASIGNADO========


class ProgresoTema(models.Model):
    tema_asignado = models.OneToOneField(TemaAsignado, on_delete=models.CASCADE) # progreso puede pertetenecer a un tema asignado 
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tema_asignado} {self.porcentaje}%"
#**********TABLA PROGRESO DEL TEMA ASIGNADO********



#==========TABLA ACTIVIDADES========


class Actividad(models.Model):
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="actividades_creadas",
    )
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT) # muchas actividades pueden tener un tema asignado 
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    nivel = models.ForeignKey(NivelAprendizaje, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo
#**********TABLA ACTIVIDADES********



#==========TABLA ACTIVIDADES ASIGNADAS========


class ActividadAsignada(models.Model):
    asignada_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="actividades_asignadas",
    )
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE) 
    actividad = models.ForeignKey(Actividad, on_delete=models.PROTECT) # muchas actividades pueden ser asignadas a una matricula  
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["matricula", "actividad"],
            name="unique_actividad_asignada"
        )
    ]
    def __str__(self):
        if self.matricula and self.actividad:
            return f"{self.matricula.estudiante} - {self.actividad.titulo}"
        return "Actividad asignada sin matrícula"


class RetroalimentacionDocente(models.Model):
    """Observación formativa del docente, aislada por matrícula autorizada."""
    matricula = models.ForeignKey(
        Matricula, on_delete=models.CASCADE, related_name="retroalimentaciones_docentes"
    )
    docente = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="retroalimentaciones_emitidas"
    )
    texto = models.TextField(max_length=1000)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-pk"]

#**********TABLA ACTIVIDADES ASIGNADAS********



#===========TABLA CARRERAS==============