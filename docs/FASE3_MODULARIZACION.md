# Fase 3 — Modularización interna

La fase separa responsabilidades sin cambiar los nombres públicos que consumen
las vistas, las rutas ni las migraciones existentes.

## Límites actuales

- **Modelos:** las definiciones se organizan en `Principal/modelos/` por
  identidad, académico, aprendizaje, vocacional, chat, evaluaciones y
  planificación. `Principal/models.py` conserva la fachada histórica.
- **Formularios:** las definiciones se organizan en
  `Principal/formularios/`; `Principal/forms.py` conserva las importaciones
  anteriores. Los formularios de banco, intervención y cuenta avanzada siguen
  en sus módulos especializados.
- **URLs:** las colecciones de portal académico, administración y cuenta viven
  en `Principal/url_modules/`; `Principal/urls.py` solo compone el listado
  final.
- **Selectores:** las consultas de identidad y académicas viven en
  `Principal/consultas/`; `Principal/view_modules/selectores.py` conserva
  la fachada que ya usan las vistas.
- **Servicios de dominio:** `Principal/services/perfiles.py` concentra la
  obtención de relaciones y la actualización transaccional del perfil.

## Compatibilidad y límites

No se modifican nombres de modelos, nombres de formularios, nombres de rutas ni
el `app_label` de Django. Por eso no se requiere una migración de base de
datos para esta refactorización. La siguiente etapa puede extraer gradualmente
otros servicios de dominio de las vistas más grandes, manteniendo el mismo
patrón de fachada.
