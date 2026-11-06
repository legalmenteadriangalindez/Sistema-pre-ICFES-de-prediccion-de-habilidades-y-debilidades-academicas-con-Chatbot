from .models import PerfilUsuario


def roles_navegacion(request):
    if not request.user.is_authenticated:
        return {'menu_docente': False, 'menu_acudiente': False, 'menu_admin': False}
    nombres = set(PerfilUsuario.objects.filter(user=request.user).values_list('roles__nombre', flat=True))
    return {
        'menu_docente': 'DOCENTE' in nombres,
        'menu_acudiente': 'ACUDIENTE' in nombres,
        'menu_admin': request.user.is_superuser or 'ADMIN' in nombres,
    }
