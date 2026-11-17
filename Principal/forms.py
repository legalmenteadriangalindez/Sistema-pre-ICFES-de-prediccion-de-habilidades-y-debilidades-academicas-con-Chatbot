"""Fachada pública de formularios organizada por dominio.

El código existente puede seguir usando `Principal.forms`; las definiciones
están en `Principal.formularios` para evitar un archivo monolítico.
"""

from .formularios.academico import (
    BoletinForm,
    EstudianteForm,
    NotaForm,
    ObservacionForm,
    PersonaForm,
    RegistroEstudianteForm,
)
from .formularios.aprendizaje import (
    ActividadForm,
    EstiloAprendizajeForm,
    NivelAprendizajeForm,
    PerfilPedagogicoForm,
    PreferenciaAccesibilidadForm,
    PrediccionRiesgoForm,
    RecomendacionForm,
    RiesgoForm,
    RitmoAprendizajeForm,
    ProgresoTemaForm,
    TemaAsignadoForm,
    TemaForm,
)
from .formularios.catalogos import (
    AcudienteForm,
    AnioLectivoForm,
    AsignarAcudienteForm,
    CursoForm,
    GradoForm,
    MateriaForm,
    RelacionAcudienteForm,
    RolForm,
    SexoForm,
)
from .formularios.cuentas import UserRegisterForm

__all__ = (
    "SexoForm",
    "RelacionAcudienteForm",
    "GradoForm",
    "AnioLectivoForm",
    "AcudienteForm",
    "AsignarAcudienteForm",
    "CursoForm",
    "MateriaForm",
    "NotaForm",
    "BoletinForm",
    "ObservacionForm",
    "UserRegisterForm",
    "PersonaForm",
    "RegistroEstudianteForm",
    "EstudianteForm",
    "RolForm",
    "RitmoAprendizajeForm",
    "EstiloAprendizajeForm",
    "NivelAprendizajeForm",
    "PerfilPedagogicoForm",
    "RiesgoForm",
    "PrediccionRiesgoForm",
    "RecomendacionForm",
    "PreferenciaAccesibilidadForm",
    "TemaForm",
    "TemaAsignadoForm",
    "ProgresoTemaForm",
    "ActividadForm",
)
