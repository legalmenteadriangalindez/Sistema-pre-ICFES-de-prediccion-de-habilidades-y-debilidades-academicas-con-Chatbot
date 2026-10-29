#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python_bin="${PYTHON_BIN:-}"
if [[ -z "$python_bin" ]]; then
    for candidate in python3.12 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            python_bin="$candidate"
            break
        fi
    done
fi

if [[ -z "$python_bin" ]] || ! "$python_bin" -c 'import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 14) else 1)'; then
    echo "Pre-ICFES requiere Python 3.12 o 3.13. Instala Python 3.12 y vuelve a ejecutar este archivo." >&2
    exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
    "$python_bin" -m venv .venv
fi

venv_python=".venv/bin/python"
if command -v sha256sum >/dev/null 2>&1; then
    requirements_hash="$(sha256sum requirements.txt)"
else
    requirements_hash="$(shasum -a 256 requirements.txt)"
fi
requirements_hash="${requirements_hash%% *}"
hash_file=".venv/.requirements-hash"
installed_hash=""
if [[ -f "$hash_file" ]]; then
    installed_hash="$(<"$hash_file")"
fi

if [[ "$installed_hash" != "$requirements_hash" ]]; then
    echo "Instalando dependencias. La primera instalación puede tardar varios minutos..."
    "$venv_python" -m pip install --upgrade pip
    "$venv_python" -m pip install -r requirements.txt
    printf '%s' "$requirements_hash" > "$hash_file"
fi

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Se creó .env con valores seguros para desarrollo local."
fi

"$venv_python" manage.py migrate

echo
echo "Aplicación disponible en http://127.0.0.1:8000"
echo "Para usar la IA, instala Ollama y ejecuta: ollama pull llama3:8b"
echo "Detén el servidor con Ctrl+C."
exec "$venv_python" manage.py runserver 127.0.0.1:8000
