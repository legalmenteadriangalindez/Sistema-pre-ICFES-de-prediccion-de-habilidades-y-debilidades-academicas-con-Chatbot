"""Predicción prudente de desempeño en la *siguiente* evaluación de un área.

Problema: clasificar si la siguiente evaluación de esa materia tendrá <60 %
de respuestas correctas. Solo se utilizan exámenes *anteriores* como entrada.
Esta tarea NO predice el puntaje oficial ICFES, ni diagnostica capacidades.
No se entrena ni publica nada con datos ficticios o muestras insuficientes.
"""
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from uuid import uuid4

from django.conf import settings
from django.utils import timezone as django_timezone

from Principal.models import RespuestaEvaluacion
from .seguimiento import AREAS_BASE

VERSION = "proxima-evaluacion-por-area-v1"
LIMITE_BAJO = 0.60
MIN_PREGUNTAS = 5
MIN_HISTORIA = 2
MIN_ESTUDIANTES = 40
MIN_EJEMPLOS = 150
MIN_POR_CLASE = 30
CUENTAS_FICTICIAS = (
    "admin_demo", "estudiante_ana", "estudiante_luis",
    "docente_demo", "acudiente_demo",
)
CARACTERISTICAS = (
    "ultimo_porcentaje", "promedio_previo", "tendencia",
    "variabilidad_ultimos_tres", "cantidad_anteriores",
    "preguntas_ultima", "dias_desde_penultima",
) + tuple("area_" + str(i) for i in range(len(AREAS_BASE)))


def _area(materia, competencia):
    if materia in ("Simulacro: Integral", "Simulacro: Integral ampliado"):
        nombre = competencia.split(" · ", 1)[0].strip()
    elif materia.startswith("Simulacro: "):
        nombre = materia.partition(": ")[2].strip()
    else:
        nombre = materia.strip()
    return nombre if nombre in AREAS_BASE else None


def extraer_eventos(estudiante_id=None):
    """Agrega respuestas por (estudiante, intento, área) sin datos demográficos.

    Un integral produce eventos separados por área. Se descartan áreas con
    menos de 5 preguntas porque su porcentaje es demasiado inestable.
    """
    filas = RespuestaEvaluacion.objects.exclude(
        intento__estudiante__persona__perfil_user__user__username__in=CUENTAS_FICTICIAS
    ).values_list(
        "intento__estudiante_id", "intento_id", "intento__fecha",
        "intento__materia", "competencia", "es_correcta",
    ).order_by("intento__fecha", "intento_id", "numero")
    if estudiante_id is not None:
        filas = filas.filter(intento__estudiante_id=estudiante_id)
    agregados = {}
    for alumno, intento, fecha, materia, competencia, correcta in filas.iterator(chunk_size=2000):
        area = _area(materia, competencia)
        if not area:
            continue
        clave = (alumno, intento, area)
        if clave not in agregados:
            agregados[clave] = {
                "fecha": fecha, "intento_id": intento, "area": area,
                "total": 0, "aciertos": 0,
            }
        agregados[clave]["total"] += 1
        agregados[clave]["aciertos"] += int(correcta)

    historiales = defaultdict(lambda: defaultdict(list))
    for (alumno, _, area), evento in agregados.items():
        if evento["total"] >= MIN_PREGUNTAS:
            historiales[alumno][area].append(evento)
    for areas in historiales.values():
        for eventos in areas.values():
            eventos.sort(key=lambda e: (e["fecha"], e["intento_id"]))
    return historiales


def _vector(historial, area):
    """Solo lee pasado; no recibe el resultado de la evaluación siguiente."""
    if len(historial) < MIN_HISTORIA:
        raise ValueError("Se requieren al menos dos evaluaciones anteriores de la misma materia.")
    tasas = [e["aciertos"] / e["total"] for e in historial]
    ultimas = tasas[-3:]
    penultima = historial[-2]["fecha"]
    ultima = historial[-1]["fecha"]
    dias = max(0, min(365, int((ultima - penultima).total_seconds() / 86400)))
    return [
        tasas[-1],
        sum(tasas) / len(tasas),
        tasas[-1] - tasas[-2],
        pstdev(ultimas),
        min(len(historial), 20),
        min(historial[-1]["total"], 50),
        dias,
    ] + [int(area == codigo) for codigo in AREAS_BASE]


def construir_muestras(historiales):
    """Cada X usa eventos 0..t-1 y cada y usa SOLO el evento t."""
    x, y, grupos = [], [], []
    for alumno, areas in historiales.items():
        for area, eventos in areas.items():
            for i in range(MIN_HISTORIA, len(eventos)):
                x.append(_vector(eventos[:i], area))
                futuro = eventos[i]
                y.append(int(futuro["aciertos"] / futuro["total"] < LIMITE_BAJO))
                grupos.append(alumno)
    return x, y, grupos


def auditar_datos(historiales=None):
    historiales = extraer_eventos() if historiales is None else historiales
    x, y, grupos = construir_muestras(historiales)
    total_estudiantes = len(set(grupos))
    positivos = sum(y)
    condiciones = {
        "estudiantes": total_estudiantes >= MIN_ESTUDIANTES,
        "ejemplos": len(y) >= MIN_EJEMPLOS,
        "casos_riesgo": positivos >= MIN_POR_CLASE,
        "casos_sin_riesgo": len(y) - positivos >= MIN_POR_CLASE,
    }
    return {
        "estudiantes": total_estudiantes,
        "eventos_calificables": sum(
            len(eventos) for areas in historiales.values() for eventos in areas.values()
        ),
        "ejemplos": len(y),
        "casos_riesgo": positivos,
        "casos_sin_riesgo": len(y) - positivos,
        "requisitos": {
            "estudiantes": MIN_ESTUDIANTES, "ejemplos": MIN_EJEMPLOS,
            "casos_por_clase": MIN_POR_CLASE,
            "preguntas_por_evento": MIN_PREGUNTAS,
            "evaluaciones_previas_por_materia": MIN_HISTORIA,
        },
        "condiciones": condiciones,
        "suficiente_para_intentar": all(condiciones.values()),
    }


def _metricas(verdaderos, estimados, probabilidades):
    from sklearn.metrics import (
        balanced_accuracy_score, brier_score_loss, confusion_matrix,
        f1_score, precision_score, recall_score, roc_auc_score,
    )
    tn, fp, fn, tp = confusion_matrix(verdaderos, estimados, labels=[0, 1]).ravel()
    return {
        "precision_riesgo": round(float(precision_score(verdaderos, estimados, zero_division=0)), 4),
        "recuperacion_riesgo": round(float(recall_score(verdaderos, estimados, zero_division=0)), 4),
        "f1_riesgo": round(float(f1_score(verdaderos, estimados, zero_division=0)), 4),
        "exactitud_balanceada": round(float(balanced_accuracy_score(verdaderos, estimados)), 4),
        "error_brier": round(float(brier_score_loss(verdaderos, probabilidades)), 4),
        "auc_roc": round(float(roc_auc_score(verdaderos, probabilidades)), 4),
        "matriz": {"vn": int(tn), "fp": int(fp), "fn": int(fn), "vp": int(tp)},
    }


def _resultado_no_publicable(motivo, auditoria, evaluacion=None):
    return {
        "publicado": False, "motivo": motivo,
        "datos": auditoria, "evaluacion": evaluacion,
    }


def entrenar_y_evaluar():
    """Entrena solo tras comprobar volumen, clases y estudiantes independientes.

    25 % de estudiantes completamente excluidos del entrenamiento y de la
    selección de hiperparámetros. Publica si supera clase mayoritaria por
    >= 0.05 en exactitud balanceada, con precisión y recall >= 0.55.
    El artefacto final se ajusta sobre TODOS los ejemplos después del test.
    """
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    historiales = extraer_eventos()
    auditoria = auditar_datos(historiales)
    if not auditoria["suficiente_para_intentar"]:
        return _resultado_no_publicable(
            "No hay suficientes estudiantes, intentos o ejemplos de ambas clases.", auditoria
        )
    x, y, grupos = construir_muestras(historiales)
    train_idx, test_idx = next(GroupShuffleSplit(
        n_splits=1, test_size=0.25, random_state=42
    ).split(x, y, groups))
    x_train, y_train = [x[i] for i in train_idx], [y[i] for i in train_idx]
    x_test, y_test = [x[i] for i in test_idx], [y[i] for i in test_idx]
    train_students = len({grupos[i] for i in train_idx})
    test_students = len({grupos[i] for i in test_idx})
    if (train_students < 25 or test_students < 8
            or min(sum(y_train), len(y_train) - sum(y_train)) < 20
            or min(sum(y_test), len(y_test) - sum(y_test)) < 6):
        return _resultado_no_publicable(
            "La separación por alumnos dejó clases o grupos insuficientes; no se publicará.",
            auditoria,
        )

    pipeline = Pipeline([
        ("escalar", StandardScaler()),
        ("clasificador", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(x_train, y_train)
    probs = pipeline.predict_proba(x_test)[:, 1].tolist()
    estimados = [int(p >= 0.5) for p in probs]
    metricas = _metricas(y_test, estimados, probs)

    referencia = DummyClassifier(strategy="most_frequent")
    referencia.fit(x_train, y_train)
    base_est = referencia.predict(x_test).tolist()
    base_probs = referencia.predict_proba(x_test)[:, list(referencia.classes_).index(1)].tolist()
    metricas_base = _metricas(y_test, base_est, base_probs)

    # No extrapolar alertas a materias sin alumnos y ambas clases
    # representados de forma independiente en entrenamiento y prueba.
    areas_validadas = []
    validacion_por_area = {}
    for numero, area in enumerate(AREAS_BASE):
        ent = [i for i in train_idx if x[i][7 + numero] == 1]
        pru = [i for i in test_idx if x[i][7 + numero] == 1]
        etiquetas_train = [y[i] for i in ent]
        etiquetas_test = [y[i] for i in pru]
        cumple = (
            len(ent) >= 15 and len(pru) >= 6
            and len({grupos[i] for i in ent}) >= 8
            and len({grupos[i] for i in pru}) >= 4
            and min(sum(etiquetas_train), len(ent) - sum(etiquetas_train)) >= 5
            and min(sum(etiquetas_test), len(pru) - sum(etiquetas_test)) >= 2
        )
        if cumple:
            posiciones = [list(test_idx).index(i) for i in pru]
            por_area = _metricas(
                etiquetas_test, [estimados[p] for p in posiciones],
                [probs[p] for p in posiciones],
            )
            cumple = (
                por_area["precision_riesgo"] >= 0.50
                and por_area["recuperacion_riesgo"] >= 0.50
                and por_area["exactitud_balanceada"] >= 0.55
            )
            if cumple:
                areas_validadas.append(area)
            validacion_por_area[area] = {
                "ejemplos_prueba": len(pru),
                "estudiantes_prueba": len({grupos[i] for i in pru}),
                "aprobada": cumple, "metricas": por_area,
            }
        else:
            validacion_por_area[area] = {
                "ejemplos_prueba": len(pru),
                "estudiantes_prueba": len({grupos[i] for i in pru}),
                "aprobada": False,
            }

    evaluacion = {
        "areas_validadas": areas_validadas,
        "evaluacion_por_area": validacion_por_area,
        "prueba_estudiantes": test_students,
        "entrenamiento_estudiantes": train_students,
        "prueba_ejemplos": len(y_test),
        "entrenamiento_ejemplos": len(y_train),
        "prueba_riesgos": int(sum(y_test)),
        "metricas": metricas,
        "referencia_mayoritaria": metricas_base,
    }
    if (
        not areas_validadas
        or metricas["exactitud_balanceada"] < metricas_base["exactitud_balanceada"] + 0.05
        or metricas["precision_riesgo"] < 0.55
        or metricas["recuperacion_riesgo"] < 0.55
    ):
        return _resultado_no_publicable(
            "El modelo no supera los criterios de precisión, recuperación y referencia.", auditoria, evaluacion
        )

    pipeline.fit(x, y)
    escalador = pipeline.named_steps["escalar"]
    clasificador = pipeline.named_steps["clasificador"]
    ahora = datetime.now(timezone.utc).isoformat()
    documento = {
        "version": VERSION, "entrenado_en": ahora,
        "objetivo": "riesgo de <60% en próxima evaluación de la misma materia",
        "umbral_alerta": 0.5, "preguntas_minimas": MIN_PREGUNTAS,
        "caracteristicas": list(CARACTERISTICAS),
        "media": escalador.mean_.tolist(),
        "escala": escalador.scale_.tolist(),
        "coeficientes": clasificador.coef_[0].tolist(),
        "intercepto": float(clasificador.intercept_[0]),
        "auditoria": auditoria, "evaluacion": evaluacion,
        "areas_validadas": areas_validadas,
    }
    ruta = Path(settings.PREDICCION_MODELO_PATH)
    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporal = ruta.with_name(ruta.name + "." + uuid4().hex + ".tmp")
    try:
        with open(temporal, "x", encoding="utf-8") as salida:
            json.dump(documento, salida, ensure_ascii=False, indent=2)
        os.chmod(temporal, 0o600)
        os.replace(temporal, ruta)
    finally:
        if temporal.exists():
            temporal.unlink()
    return {"publicado": True, "motivo": "Modelo evaluado y actualizado.",
            "datos": auditoria, "evaluacion": evaluacion}


def cargar_modelo():
    """JSON estricto sin pickle; ignorar artefactos corruptos o incompatibles."""
    ruta = Path(settings.PREDICCION_MODELO_PATH)
    try:
        if not ruta.is_file() or ruta.stat().st_size > 128 * 1024:
            return None
        with ruta.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if (datos.get("version") != VERSION
                or datos.get("caracteristicas") != list(CARACTERISTICAS)
                or not isinstance(datos.get("areas_validadas"), list)
                or not datos["areas_validadas"]
                or any(a not in AREAS_BASE for a in datos["areas_validadas"])):
            return None
        if len(datos["media"]) != len(CARACTERISTICAS):
            return None
        if len(datos["escala"]) != len(CARACTERISTICAS):
            return None
        if len(datos["coeficientes"]) != len(CARACTERISTICAS):
            return None
        if not all(
            math.isfinite(float(v))
            for k in ("media", "escala", "coeficientes")
            for v in datos[k]
        ) or not math.isfinite(float(datos["intercepto"])):
            return None
        if any(float(e) <= 0 for e in datos["escala"]):
            return None
        fecha = datetime.fromisoformat(datos["entrenado_en"])
        if fecha.tzinfo is None or (
            datetime.now(timezone.utc) - fecha
        ).total_seconds() > 180 * 86400:
            return None
        return datos
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return None


def _probabilidad(modelo, vector):
    valor = float(modelo["intercepto"])
    for x, media, escala, coef in zip(
        vector, modelo["media"], modelo["escala"], modelo["coeficientes"]
    ):
        valor += ((x - float(media)) / float(escala)) * float(coef)
    if valor >= 0:
        return 1 / (1 + math.exp(-valor))
    exponente = math.exp(valor)
    return exponente / (1 + exponente)


def predicciones_estudiante(estudiante, modelo=None, historiales=None):
    """Emite alertas cualitativas para el próximo intento, nunca notas futuras."""
    modelo = cargar_modelo() if modelo is None else modelo
    if not modelo:
        return []
    historiales = extraer_eventos(estudiante.pk) if historiales is None else historiales
    areas = historiales.get(estudiante.pk, {})
    resultado = []
    for area in AREAS_BASE:
        eventos = areas.get(area, [])
        if area not in modelo["areas_validadas"] or len(eventos) < MIN_HISTORIA:
            continue
        prob = _probabilidad(modelo, _vector(eventos, area))
        resultado.append({
            "area": area,
            "evaluaciones_previas": len(eventos),
            "ultima_fecha": eventos[-1]["fecha"],
            "ultimo_porcentaje": round(
                100 * eventos[-1]["aciertos"] / eventos[-1]["total"], 1
            ),
            "alerta": prob >= float(modelo["umbral_alerta"]),
            # No presentar valores probabilísticos como probabilidades calibradas.
            "mensaje": ("Priorizar práctica en esta materia" if prob >= float(modelo["umbral_alerta"])
                        else "Mantener práctica y seguimiento"),
        })
    return resultado
