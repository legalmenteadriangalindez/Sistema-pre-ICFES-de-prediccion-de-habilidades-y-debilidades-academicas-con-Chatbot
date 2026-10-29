$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonCommand = $null
$pythonArguments = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -c "import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 14) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = "py"
        $pythonArguments = @("-3.12")
    }
}

if (-not $pythonCommand -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonCommand = "python"
}

if (-not $pythonCommand) {
    throw "Instala Python 3.12 desde https://www.python.org/downloads/ y vuelve a ejecutar este archivo."
}

& $pythonCommand @pythonArguments -c "import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 14) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Pre-ICFES requiere Python 3.12 o 3.13. Instala Python 3.12 y vuelve a ejecutar este archivo."
}

if (-not (Test-Path ".venv")) {
    & $pythonCommand @pythonArguments -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual de Python." }
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$requirementsHash = (Get-FileHash "requirements.txt" -Algorithm SHA256).Hash
$hashFile = Join-Path $PSScriptRoot ".venv\.requirements-hash"
$installedHash = if (Test-Path $hashFile) { (Get-Content $hashFile -Raw).Trim() } else { "" }

if ($installedHash -ne $requirementsHash) {
    Write-Host "Instalando dependencias. La primera instalación puede tardar varios minutos..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "No se pudo actualizar pip." }
    & $venvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias. Revisa la conexión y vuelve a intentar." }
    Set-Content -Path $hashFile -Value $requirementsHash -NoNewline
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creó .env con valores seguros para desarrollo local."
}

& $venvPython manage.py migrate
if ($LASTEXITCODE -ne 0) { throw "No se pudieron preparar las tablas de la base local." }

Write-Host ""
Write-Host "Aplicación disponible en http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Para usar la IA, instala Ollama y ejecuta: ollama pull llama3:8b"
Write-Host "Detén el servidor con Ctrl+C."
& $venvPython manage.py runserver 127.0.0.1:8000
