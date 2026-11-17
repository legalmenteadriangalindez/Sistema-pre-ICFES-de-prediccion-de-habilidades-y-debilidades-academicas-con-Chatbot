"""Modelos de orientación vocacional y materiales de estudio."""

from django.db import models

from .academico import Matricula
from .aprendizaje import Tema


class Carrera(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
#***********TABLA CARRERAS**************



#==========TABLA RECOMENDACION VOCACIONAL==========


class RecomendacionVocacional(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, null=True, blank=True) # muchas recomendaciones vocacionales pueden pertenecer a una matricula 
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    compatibilidad = models.DecimalField(max_digits=5, decimal_places=2)
    conocimientos_necesarios = models.TextField()
    puntaje_requerido = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.matricula and self.carrera:
            return f"{self.matricula.estudiante} - {self.carrera}"
        return "Recomendación vocacional sin matrícula"

#**********TABLA RECOMENDACION VOCACIONAL***********



#===========TABLA MATERIALES ===============


class MaterialEstudio(models.Model):
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT) # muchos materiales pueden perteneser a un tema 
    titulo = models.CharField(max_length=100)
    url = models.URLField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo
#*************TABLA MATERIALES*****************



#==========TABLA MATERIALES ASIGNADOS=======


class MaterialAsignado(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, null=True, blank=True) # muchos materiales pueden ser asignados a una matricula 
    material = models.ForeignKey(MaterialEstudio, on_delete=models.PROTECT)
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matricula","material"],
                name="unique_material_asignado"
            )
        ]
#**********TABLA MATERIALES ASIGNADOS*******



#=============TABLA CONVERSACIONES==============