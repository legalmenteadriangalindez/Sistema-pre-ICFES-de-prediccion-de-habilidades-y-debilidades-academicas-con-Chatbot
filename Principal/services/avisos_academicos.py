"""Avisos internos por eventos reales, sin correos ni mensajes masivos."""
from Principal.models import NotificacionAcademica, PreferenciaAvisos


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
