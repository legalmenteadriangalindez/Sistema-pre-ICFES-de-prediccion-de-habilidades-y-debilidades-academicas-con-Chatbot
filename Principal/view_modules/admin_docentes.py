"""Concesión y revocación administrativa de cursos de docentes."""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from Principal.models import AnioLectivo, AsignacionDocenteCurso, Curso, PerfilUsuario
from .selectores import es_gestor

@login_required
@user_passes_test(es_gestor, login_url='/accounts/login/')
def gestion_docentes(request):
    """Solo administradores conceden y revocan acceso a cursos docentes."""
    error = None
    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion == "revocar":
            raw = request.POST.get("asignacion_id", "")
            if raw.isdecimal():
                AsignacionDocenteCurso.objects.filter(pk=int(raw)).update(activo=False)
                return redirect("admin_asignaciones_docentes")
            error = "Selecciona una asignación válida."
        elif accion == "asignar":
            raw_usuario = request.POST.get("docente", "")
            raw_curso = request.POST.get("curso", "")
            raw_anio = request.POST.get("anio_lectivo", "")
            if all(c.isdecimal() for c in (raw_usuario, raw_curso, raw_anio)):
                docente = PerfilUsuario.objects.filter(
                    user_id=int(raw_usuario), user__is_active=True,
                    roles__nombre__iexact="DOCENTE"
                ).first()
                curso = Curso.objects.filter(pk=int(raw_curso), activo=True).first()
                anio = AnioLectivo.objects.filter(pk=int(raw_anio)).first()
                if docente and curso and anio:
                    asignacion, creada = AsignacionDocenteCurso.objects.get_or_create(
                        docente=docente, curso=curso, anio_lectivo=anio,
                        defaults={"activo": True},
                    )
                    if not creada and not asignacion.activo:
                        asignacion.activo = True
                        asignacion.save(update_fields=["activo"])
                    return redirect("admin_asignaciones_docentes")
            error = "Selecciona un docente activo, curso activo y año lectivo válidos."
        else:
            error = "Acción no permitida."

    return render(request, "AdminAsignacionesDocentes.html", {
        "error": error,
        "docentes": PerfilUsuario.objects.filter(
            user__is_active=True, roles__nombre__iexact="DOCENTE"
        ).select_related("user").distinct().order_by("user__username"),
        "cursos": Curso.objects.filter(activo=True).select_related("grado").order_by("grado__nombre", "nombre"),
        "anios": AnioLectivo.objects.all().order_by("-anio"),
        "asignaciones": AsignacionDocenteCurso.objects.select_related(
            "docente__user", "curso__grado", "anio_lectivo"
        ).order_by("-activo", "docente__user__username", "-anio_lectivo__anio"),
    })

