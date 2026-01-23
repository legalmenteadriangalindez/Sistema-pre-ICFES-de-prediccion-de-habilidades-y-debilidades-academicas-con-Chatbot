from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Persona)
admin.site.register(Estudiante)
admin.site.register(Nota)
admin.site.register(Observacion)
admin.site.register(RelacionAcudiente)
admin.site.register(Acudiente)
admin.site.register(AnioLectivo)
admin.site.register(Materia)
admin.site.register(Docente)
admin.site.register(AsignacionDocente)
admin.site.register(PeriodoAcademico)
admin.site.register(PerfilUsuario)
admin.site.register(Grado)
admin.site.register(Jornada)
admin.site.register(Curso)
admin.site.register(Sede)
admin.site.register(Sexo)
admin.site.register(Rol)