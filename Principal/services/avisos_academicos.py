"""Avisos internos por eventos reales, sin correos ni mensajes masivos."""
from Principal.models import EstudianteAcudiente, NotificacionAcademica, PreferenciaAvisos


def emitir_aviso(usuario, categoria, titulo, mensaje, clave):
    if usuario is None or not usuario.is_active:
        return None
    preferencias = PreferenciaAvisos.objects.filter(usuario=usuario).first()
    if preferencias and not preferencias.recibir_avisos:
        return None
    aviso, _ = NotificacionAcademica.objects.get_or_create(
        usuario=usuario, clave=clave[:100],
        defaults={
            "categoria": categoria[:32],
            "titulo": titulo[:140],
            "mensaje": mensaje[:500],
        },
    )
    return aviso


def emitir_aviso_familiar(estudiante, categoria, mensaje, clave):
    """Solo acudientes vinculados que activaron avisos familiares."""
    vinculados = EstudianteAcudiente.objects.filter(
        estudiante=estudiante,
    ).select_related("acudiente__persona__perfil_user__user")
    for vinculo in vinculados:
        usuario = vinculo.acudiente.persona.perfil_user.user
        preferencias = PreferenciaAvisos.objects.filter(usuario=usuario).first()
        if not preferencias or not preferencias.avisos_familiares:
            continue
        emitir_aviso(
            usuario, categoria, "Aviso de acompañamiento familiar",
            mensaje, f"familia-{clave}",
        )
