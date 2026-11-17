"""Fachada pública de modelos organizada por dominios.

Las clases viven en :mod:`Principal.modelos`, pero este módulo conserva la
API histórica `Principal.models`. Así no se modifican imports, migraciones ni
las relaciones que ya utiliza la aplicación.
"""

from .modelos.academico import (
    AnioLectivo,
    AsignacionDocenteCurso,
    Boletin,
    Curso,
    Estudiante,
    EstudianteAcudiente,
    Grado,
    Materia,
    Matricula,
    Nota,
    Observacion,
)
from .modelos.aprendizaje import (
    Actividad,
    ActividadAsignada,
    AnalisisCognitivo,
    EstiloAprendizaje,
    NivelAprendizaje,
    PerfilPedagogico,
    PreferenciaAccesibilidad,
    PrediccionRiesgo,
    Recomendacion,
    RetroalimentacionDocente,
    Riesgo,
    RitmoAprendizaje,
    ProgresoTema,
    Tema,
    TemaAsignado,
)
from .modelos.chat import Conversacion, Mensaje, RolMessage
from .modelos.evaluaciones import IntentoEvaluacion, RespuestaEvaluacion
from .modelos.identidad import (
    Acudiente,
    PerfilUsuario,
    Persona,
    RelacionAcudiente,
    Rol,
    Sexo,
)
from .modelos.planificacion import PlanEstudioSemanal, SesionPlanSemanal
from .modelos.vocacional import (
    Carrera,
    MaterialAsignado,
    MaterialEstudio,
    RecomendacionVocacional,
)

# Estos modelos ya estaban separados y conservan sus módulos especializados.
from .alta_prioridad_models import IntervencionAcademica, SimulacroAvanzado
from .banco_models import PreguntaBanco
from .funciones_pendientes_models import (
    ConsentimientoTutorIA,
    NotificacionAcademica,
    PreferenciaAvisos,
    RegistroAuditoria,
    RepasoEspaciado,
)

__all__ = (
    "Rol",
    "PerfilUsuario",
    "Sexo",
    "Persona",
    "RelacionAcudiente",
    "Acudiente",
    "Grado",
    "Curso",
    "AnioLectivo",
    "Materia",
    "Estudiante",
    "EstudianteAcudiente",
    "Matricula",
    "Nota",
    "AsignacionDocenteCurso",
    "Boletin",
    "Observacion",
    "RitmoAprendizaje",
    "EstiloAprendizaje",
    "NivelAprendizaje",
    "PerfilPedagogico",
    "AnalisisCognitivo",
    "Riesgo",
    "PrediccionRiesgo",
    "Recomendacion",
    "PreferenciaAccesibilidad",
    "Tema",
    "TemaAsignado",
    "ProgresoTema",
    "Actividad",
    "ActividadAsignada",
    "RetroalimentacionDocente",
    "Carrera",
    "RecomendacionVocacional",
    "MaterialEstudio",
    "MaterialAsignado",
    "Conversacion",
    "RolMessage",
    "Mensaje",
    "IntentoEvaluacion",
    "RespuestaEvaluacion",
    "PlanEstudioSemanal",
    "SesionPlanSemanal",
    "PreguntaBanco",
    "IntervencionAcademica",
    "SimulacroAvanzado",
    "ConsentimientoTutorIA",
    "NotificacionAcademica",
    "PreferenciaAvisos",
    "RegistroAuditoria",
    "RepasoEspaciado",
)
