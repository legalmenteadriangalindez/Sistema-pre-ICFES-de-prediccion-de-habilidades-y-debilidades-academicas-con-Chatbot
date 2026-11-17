#!/usr/bin/env python3
"""Auditoría estática y reproducible de la Fase 1 del proyecto Pre-ICFES.

El script no importa Django ni modifica archivos. Su objetivo es generar un
inventario conservador de referencias, rutas y consultas potencialmente
repetidas para apoyar una limpieza posterior sin cambiar comportamiento.
"""

from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = ROOT / "Principal" / "templates"
CSS_ROOT = ROOT / "Principal" / "static" / "css"
JS_ROOT = ROOT / "Principal" / "static" / "js"

TEXT_SUFFIXES = {
    ".py", ".html", ".css", ".js", ".cjs", ".md", ".toml", ".yml", ".yaml", ".txt"
}
QUERY_METHODS = {
    "all", "annotate", "bulk_create", "count", "create", "delete", "exists",
    "filter", "first", "get", "get_or_create", "last", "latest", "aggregate",
    "prefetch_related", "select_related", "update", "update_or_create",
}
TEMPLATE_RE = re.compile(
    r"{%\s*(?:extends|include)\s+[\"']([^\"']+)[\"']", re.IGNORECASE
)
RENDER_RE = re.compile(
    r"\b(?:render|render_to_response)\s*\([^)]*?[\"']([^\"']+\.html)[\"']",
    re.IGNORECASE | re.DOTALL,
)
TEMPLATE_NAME_RE = re.compile(
    r"\btemplate_name\s*=\s*[\"']([^\"']+\.html)[\"']",
    re.IGNORECASE,
)
STATIC_RE = re.compile(r"{%\s*static\s+[\"']([^\"']+)[\"']", re.IGNORECASE)
DIRECT_ASSET_RE = re.compile(
    r"(?:href|src|url)\s*=\s*[\"'][^\"']*?((?:css|js)/[^\"')?#]+)",
    re.IGNORECASE,
)
TEMPLATE_URL_RE = re.compile(
    r"{%\s*url\s+[\"']([^\"']+)[\"']", re.IGNORECASE
)
PY_URL_RE = re.compile(
    r"\b(?:reverse|redirect|resolve_url)\s*\(\s*[\"']([^\"']+)[\"']"
)
FOR_RE = re.compile(r"{%\s*for\s+([^%]+?)\s+in\s+([^%]+?)\s*%}", re.IGNORECASE)
END_FOR_RE = re.compile(r"{%\s*endfor\s*%}", re.IGNORECASE)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def source_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in TEXT_SUFFIXES
    ]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalize_template(value: str) -> str:
    value = value.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    if value.startswith("templates/"):
        value = value[len("templates/") :]
    return value


def normalize_asset(value: str, kind: str) -> str:
    value = value.strip().replace("\\", "/")
    value = value.split("?", 1)[0].split("#", 1)[0]
    prefix = f"{kind}/"
    if value.startswith("/static/"):
        value = value[len("/static/") :]
    if value.startswith(prefix):
        return value[len(prefix):]
    if value.startswith("/") and value[1:].startswith(prefix):
        return value[1 + len(prefix):]
    return value


def collect_reference_inventory(files: list[Path]) -> dict[str, object]:
    template_refs: dict[str, set[str]] = collections.defaultdict(set)
    css_refs: dict[str, set[str]] = collections.defaultdict(set)
    js_refs: dict[str, set[str]] = collections.defaultdict(set)

    for path in files:
        content = read_text(path)
        source = rel(path)
        for match in TEMPLATE_RE.finditer(content):
            template_refs[normalize_template(match.group(1))].add(source)
        for match in RENDER_RE.finditer(content):
            template_refs[normalize_template(match.group(1))].add(source)
        for match in TEMPLATE_NAME_RE.finditer(content):
            template_refs[normalize_template(match.group(1))].add(source)

        for match in STATIC_RE.finditer(content):
            asset = match.group(1)
            if asset.startswith("css/"):
                css_refs[normalize_asset(asset, "css")].add(source)
            elif asset.startswith("js/"):
                js_refs[normalize_asset(asset, "js")].add(source)

        for match in DIRECT_ASSET_RE.finditer(content):
            asset = match.group(1)
            if asset.lower().startswith("css/"):
                css_refs[normalize_asset(asset, "css")].add(source)
            elif asset.lower().startswith("js/"):
                js_refs[normalize_asset(asset, "js")].add(source)

    css_paths = CSS_ROOT.rglob("*.css") if CSS_ROOT.exists() else []
    for path in css_paths:
        content = read_text(path)
        source = rel(path)
        for match in re.finditer(
            r"@import\s+(?:url\(\s*)?[\"']?([^\"')\s]+)", content, re.IGNORECASE
        ):
            asset = normalize_asset(match.group(1), "css")
            css_refs[asset].add(source)

    templates = {
        path.relative_to(TEMPLATES_ROOT).as_posix()
        for path in TEMPLATES_ROOT.rglob("*.html")
    } if TEMPLATES_ROOT.exists() else set()
    css = {
        path.relative_to(CSS_ROOT).as_posix()
        for path in CSS_ROOT.rglob("*.css")
    } if CSS_ROOT.exists() else set()
    js = {
        path.relative_to(JS_ROOT).as_posix()
        for path in JS_ROOT.rglob("*.js")
    } if JS_ROOT.exists() else set()

    return {
        "templates": {
            "files": sorted(templates),
            "references": {key: sorted(value) for key, value in sorted(template_refs.items())},
            "candidates": sorted(templates - set(template_refs)),
        },
        "css": {
            "files": sorted(css),
            "references": {key: sorted(value) for key, value in sorted(css_refs.items())},
            "candidates": sorted(css - set(css_refs)),
        },
        "js": {
            "files": sorted(js),
            "references": {key: sorted(value) for key, value in sorted(js_refs.items())},
            "candidates": sorted(js - set(js_refs)),
        },
    }


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def parse_routes(files: list[Path]) -> list[dict[str, object]]:
    routes: list[dict[str, object]] = []
    for path in files:
        if path.name not in {"urls.py", "urls_admin.py"}:
            continue
        try:
            tree = ast.parse(read_text(path), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if func_name not in {"path", "re_path"} or not node.args:
                continue
            pattern = literal_string(node.args[0])
            if pattern is None:
                continue
            name = None
            for keyword in node.keywords:
                if keyword.arg == "name":
                    name = literal_string(keyword.value)
                    break
            routes.append(
                {
                    "file": rel(path),
                    "line": node.lineno,
                    "pattern": pattern,
                    "name": name or "",
                }
            )
    return sorted(routes, key=lambda item: (str(item["file"]), int(item["line"])))


def route_usage(files: list[Path]) -> set[str]:
    used: set[str] = set()
    for path in files:
        content = read_text(path)
        used.update(TEMPLATE_URL_RE.findall(content))
        used.update(PY_URL_RE.findall(content))
    return used


def duplicate_values(routes: list[dict[str, object]], key: str) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for route in routes:
        value = str(route.get(key, ""))
        if value:
            grouped[value].append(route)
    return {key: value for key, value in grouped.items() if len(value) > 1}


def query_chain(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def is_queryset_call(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in QUERY_METHODS:
        return False
    chain = query_chain(node.func.value)
    return ".objects" in chain or chain.startswith("objects")


def query_candidates(files: list[Path]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in files:
        if path.suffix != ".py":
            continue
        # Test factories intentionally issue ORM writes inside loops; they are
        # not application N+1 candidates and would drown the runtime findings.
        if (
            path.name.startswith("test_")
            or path.name == "tests.py"
            or "tests" in path.parts
            or "scripts" in path.parts
        ):
            continue
        try:
            tree = ast.parse(read_text(path), filename=str(path))
        except SyntaxError:
            continue
        for loop in [
            node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.AsyncFor))
        ]:
            for node in ast.walk(loop):
                if node is loop or not isinstance(node, ast.Call) or not is_queryset_call(node):
                    continue
                findings.append(
                    {
                        "file": rel(path),
                        "line": node.lineno,
                        "reason": "Consulta ORM dentro de un bucle; revisar posible N+1.",
                        "query": query_chain(node),
                    }
                )

    template_paths = TEMPLATES_ROOT.rglob("*.html") if TEMPLATES_ROOT.exists() else []
    for path in template_paths:
        lines = read_text(path).splitlines()
        loop_start: int | None = None
        for index, line in enumerate(lines, start=1):
            if FOR_RE.search(line):
                loop_start = index
                continue
            if loop_start is not None and END_FOR_RE.search(line):
                loop_start = None
                continue
            if loop_start is not None and re.search(
                r"{{[^}]*\b[A-Za-z_][\w-]*\.[A-Za-z_][\w-]*\.[A-Za-z_]",
                line,
            ):
                findings.append(
                    {
                        "file": rel(path),
                        "line": index,
                        "reason": "Relación anidada usada dentro de un for de plantilla; revisar prefetch.",
                        "query": line.strip()[:160],
                    }
                )
    return findings


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    if not rows:
        return "_Ninguno detectado._"
    escape = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    result = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    result.extend("| " + " | ".join(escape(value) for value in row) + " |" for row in rows)
    return "\n".join(result)


def render_report(
    inventory: dict[str, object],
    routes: list[dict[str, object]],
    used_names: set[str],
    queries: list[dict[str, object]],
) -> str:
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    route_names = [str(route["name"]) for route in routes if route["name"]]
    duplicate_names = duplicate_values(routes, "name")
    duplicate_patterns = duplicate_values(routes, "pattern")
    unused_route_names = sorted(set(route_names) - used_names)

    lines = [
        "# Inventario Fase 1 — Pre-ICFES",
        "",
        f"> Generado automáticamente por scripts/audit_phase1.py el {generated}.",
        "> El análisis es estático y conservador: un candidato sin referencia no se elimina automáticamente.",
        "",
        "## Resumen",
        "",
        f"- Plantillas HTML: {len(inventory['templates']['files'])}.",
        f"- Hojas CSS: {len(inventory['css']['files'])}.",
        f"- Módulos JavaScript: {len(inventory['js']['files'])}.",
        f"- Rutas detectadas: {len(routes)}.",
        f"- Nombres de ruta únicos: {len(set(route_names))}.",
        f"- Posibles consultas N+1: {len(queries)}.",
        "",
        "## Plantillas, CSS y JavaScript candidatos a revisión",
        "",
        "Los siguientes archivos no tienen una referencia estática detectable en plantillas, Python, CSS o documentación. Pueden ser usados dinámicamente; deben verificarse antes de eliminarse.",
        "",
        "### Plantillas",
        markdown_table(
            [[item] for item in inventory["templates"]["candidates"]],
            ["Candidato"],
        ),
        "",
        "### CSS",
        markdown_table([[item] for item in inventory["css"]["candidates"]], ["Candidato"]),
        "",
        "### JavaScript",
        markdown_table([[item] for item in inventory["js"]["candidates"]], ["Candidato"]),
        "",
        "## URLs",
        "",
        "### Nombres duplicados",
        markdown_table(
            [
                [name, "<br>".join(f"{item['file']}:{item['line']}" for item in entries)]
                for name, entries in sorted(duplicate_names.items())
            ],
            ["Nombre", "Definiciones"],
        ),
        "",
        "### Patrones duplicados",
        markdown_table(
            [
                [pattern, "<br>".join(f"{item['file']}:{item['line']} ({item['name']})" for item in entries)]
                for pattern, entries in sorted(duplicate_patterns.items())
            ],
            ["Patrón", "Definiciones"],
        ),
        "",
        "### Nombres definidos sin referencia estática",
        markdown_table([[name] for name in unused_route_names], ["Nombre candidato"]),
        "",
        "## Consultas potencialmente repetidas",
        "",
        "Son heurísticas para revisión manual; no prueban por sí solas un N+1.",
        "",
        markdown_table(
            [
                [item["file"], item["line"], item["reason"], item["query"]]
                for item in queries
            ],
            ["Archivo", "Línea", "Motivo", "Expresión"],
        ),
        "",
        "## Criterio de cierre",
        "",
        "Antes de eliminar un candidato se debe confirmar: referencias dinámicas, reversas de URL, pruebas de navegador, carga de estáticos y ausencia en despliegues anteriores.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Archivo Markdown de salida.")
    args = parser.parse_args()

    files = source_files()
    inventory = collect_reference_inventory(files)
    routes = parse_routes(files)
    used_names = route_usage(files)
    queries = query_candidates(files)
    report = render_report(inventory, routes, used_names, queries)

    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
