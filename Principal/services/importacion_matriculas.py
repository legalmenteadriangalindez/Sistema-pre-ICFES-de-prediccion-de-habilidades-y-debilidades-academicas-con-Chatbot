"""Importación controlada de matrículas existentes desde CSV/XLSX.

Nunca crea usuarios ni asocia identidades por nombres ambiguos.
"""
import csv
import io
from collections import Counter

from django.db import transaction

from Principal.models import AnioLectivo, Curso, Estudiante, Matricula

CAMPOS = ("documento", "curso_id", "anio")
MAX_FILAS = 500
MAX_BYTES = 2 * 1024 * 1024


def texto_celda(valor):
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def leer_plantilla(archivo):
    """Solo tres columnas; tamaño y filas limitados explícitamente."""
    if archivo.size > MAX_BYTES:
        raise ValueError("Máximo 2 MB por archivo.")
    nombre = archivo.name.lower()
    if nombre.endswith(".csv"):
        try:
            datos = archivo.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("El archivo CSV debe estar en UTF-8.") from exc
        cabecera = datos.splitlines()[0] if datos.splitlines() else ""
        delimitador = ";" if cabecera.count(";") > cabecera.count(",") else ","
        registros = list(csv.DictReader(io.StringIO(datos), delimiter=delimitador))
        campos = list(registros[0]) if registros else [c.strip() for c in cabecera.split(delimitador)]
    elif nombre.endswith(".xlsx"):
        from openpyxl import load_workbook

        libro = load_workbook(archivo, read_only=True, data_only=True)
        try:
            hoja = libro.active
            filas = hoja.iter_rows(max_row=MAX_FILAS + 2, values_only=True)
            encabezado = next(filas, ())
            campos = [texto_celda(valor) for valor in encabezado]
            registros = [
                dict(zip(campos, fila, strict=False)) for fila in filas
                if any(valor is not None for valor in fila)
            ]
        finally:
            libro.close()
    else:
        raise ValueError("Formato admitido: CSV UTF-8 o XLSX.")
    if set(campos) != set(CAMPOS) or len(campos) != len(CAMPOS):
        raise ValueError("Las columnas deben ser exactamente documento, curso_id, anio.")
    if not registros:
        raise ValueError("El archivo no contiene filas.")
    if len(registros) > MAX_FILAS:
        raise ValueError("Máximo 500 filas por archivo.")
    return [{k: texto_celda(registro.get(k)) for k in CAMPOS} for registro in registros]


def preparar_matriculas(filas):
    documentos = [f["documento"] for f in filas]
    if any(not doc or len(doc) > 20 for doc in documentos):
        raise ValueError("Documento vacío o demasiado largo.")
    if len(set(documentos)) != len(documentos):
        raise ValueError("El archivo repite documentos de estudiantes.")
    estudiantes = {
        e.persona.documento: e
        for e in Estudiante.objects.filter(persona__documento__in=documentos).select_related("persona")
    }
    cursos = {str(c.pk): c for c in Curso.objects.filter(activo=True)}
    anios = {str(a.anio): a for a in AnioLectivo.objects.all()}
    nuevas = []
    errores = []
    cupos = Counter()
    omitidas = 0
    for indice, fila in enumerate(filas, start=2):
        estudiante = estudiantes.get(fila["documento"])
        curso = cursos.get(fila["curso_id"])
        anio = anios.get(fila["anio"])
        if not estudiante or not curso or not anio:
            errores.append(f"Fila {indice}: documento, curso o año no reconocido.")
            continue
        existente = Matricula.objects.filter(estudiante=estudiante, anio_lectivo=anio).first()
        if existente:
            if existente.curso_id != curso.pk:
                errores.append(f"Fila {indice}: el estudiante ya tiene matrícula en otro curso ese año.")
            else:
                omitidas += 1
            continue
        nuevas.append(Matricula(
            estudiante=estudiante, curso=curso,
            anio_lectivo=anio, activa=True,
        ))
        cupos[(curso.pk, anio.pk)] += 1
    if errores:
        raise ValueError(" ".join(errores[:8]))
    for (curso_id, anio_id), cantidad in cupos.items():
        curso = cursos[str(curso_id)]
        ocupadas = Matricula.objects.filter(
            curso_id=curso_id, anio_lectivo_id=anio_id, activa=True,
        ).count()
        if ocupadas + cantidad > curso.cupo_maximo:
            raise ValueError(f"Se supera el cupo del curso {curso.pk} en el año indicado.")
    return nuevas, omitidas


@transaction.atomic
def importar_matriculas(archivo):
    filas = leer_plantilla(archivo)
    # Lock de cursos: serializa nuevas cargas bajo PostgreSQL.
    ids = sorted({int(f["curso_id"]) for f in filas if f["curso_id"].isdecimal()})
    list(Curso.objects.select_for_update().filter(pk__in=ids))
    nuevas, omitidas = preparar_matriculas(filas)
    Matricula.objects.bulk_create(nuevas)
    return len(nuevas), omitidas
