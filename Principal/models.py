from django.db import models

from django.contrib.auth.models import User

from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

#============TABLA ROL====================================
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
class IntentoEvaluacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="intentos_evaluacion")
    materia = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    total_preguntas = models.PositiveIntegerField()
    aciertos = models.PositiveIntegerField()

    @property
    def porcentaje(self):
        return round(100 * self.aciertos / self.total_preguntas, 1) if self.total_preguntas else 0


class RespuestaEvaluacion(models.Model):
    pregunta_banco = models.ForeignKey(
        "PreguntaBanco", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="respuestas_evaluacion",
    )
    intento = models.ForeignKey(IntentoEvaluacion, on_delete=models.CASCADE, related_name="respuestas")
    numero = models.PositiveIntegerField()
    competencia = models.CharField(max_length=100)
    enunciado = models.TextField()
    pregunta = models.TextField()
    opciones = models.JSONField()
    respuesta_estudiante = models.CharField(max_length=1, blank=True)
    respuesta_correcta = models.CharField(max_length=1)
    explicacion = models.TextField()
    es_correcta = models.BooleanField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["intento", "numero"], name="unique_respuesta_intento_numero")]


# ========== PLAN DE ESTUDIO SEMANAL PERSISTENTE ==========
# Se conserva el plan tal como fue propuesto; las nuevas evaluaciones no
# reescriben sesiones ni avances que el estudiante ya haya registrado.
class PlanEstudioSemanal(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="planes_semanales"
    )
    semana_inicio = models.DateField()  # Lunes de la semana
    creado_en = models.DateTimeField(auto_now_add=True)
    con_datos_academicos = models.BooleanField(default=False)

    class Meta:
        ordering = ["-semana_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "semana_inicio"],
                name="uq_plan_estudiante_semana",
            ),
        ]

    def __str__(self):
        return f"{self.estudiante} | {self.semana_inicio}"


class SesionPlanSemanal(models.Model):
    plan = models.ForeignKey(
        PlanEstudioSemanal, on_delete=models.CASCADE, related_name="sesiones"
    )
    dia_indice = models.PositiveSmallIntegerField()  # Lunes=0, domingo=6
    dia_nombre = models.CharField(max_length=12)
    fecha_programada = models.DateField()
    area = models.CharField(max_length=100)
    actividad = models.CharField(max_length=250)
    minutos_previstos = models.PositiveSmallIntegerField()
    destino = models.CharField(max_length=32, default="test")
    completada = models.BooleanField(default=False)
    minutos_realizados = models.PositiveSmallIntegerField(default=0)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    notas = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["dia_indice"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "dia_indice"],
                name="uq_sesion_plan_dia",
            ),
        ]

    def __str__(self):
        return f"{self.plan} | {self.dia_nombre}"


# Registro de modelos de banco curado; Django conserva app_label Principal.
from .banco_models import PreguntaBanco  # noqa: E402,F401
from .alta_prioridad_models import IntervencionAcademica, SimulacroAvanzado  # noqa: E402,F401
