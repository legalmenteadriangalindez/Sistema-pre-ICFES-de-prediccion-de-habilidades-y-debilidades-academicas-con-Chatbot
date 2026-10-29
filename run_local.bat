@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
if errorlevel 1 (
    echo.
    echo El arranque termino con un error. Lee el mensaje anterior.
    pause
)
