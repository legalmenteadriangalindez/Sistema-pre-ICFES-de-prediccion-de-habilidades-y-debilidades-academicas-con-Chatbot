"""Modelos de conversaciones del tutor."""

from django.contrib.auth.models import User
from django.db import models


class Conversacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
#**************TABLA CONVERSACIONES*****************



#=============TABLA ROL MESSAGES====================


class RolMessage(models.Model):
    nombre = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=50)

#*************TABLA ROL MESSAGES********************




#=======================TABLA MENSAGE=======================


class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE) # muchos mensages pueden pertenecer a una conversacion 
    rol = models.ForeignKey(RolMessage,on_delete=models.CASCADE)  
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
#*********************TABLA MENSAGE****************************


# ================== RESULTADOS DE EVALUACIONES ==================