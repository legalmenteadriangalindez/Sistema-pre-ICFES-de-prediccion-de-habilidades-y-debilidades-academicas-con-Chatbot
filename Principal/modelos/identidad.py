"""Modelos de identidad, cuentas y relaciones familiares."""

from django.contrib.auth.models import User
from django.db import models


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  # ADMIN, ESTUDIANTE, ACUDIENTE
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre
#**********TABLA ROL*************************************



#=================TABLA PERFIL DE USUARIO==============


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # un perfil puede pertenecer a un usuario
    roles = models.ManyToManyField(Rol, related_name="usuarios")  # un usuario puede tener varios roles

    def __str__(self):
        return self.user.username
#****************TABLA ERFIL DE USUARIO******************


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
    perfil_user = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"
#********************TABLA ACUDIENTE********************





#==================TABLA GRADO==================