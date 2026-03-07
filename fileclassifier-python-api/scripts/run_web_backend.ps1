$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$systemPython = "python"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv for backend..."
    & $systemPython -m venv $venvPath
}

Set-Location $projectRoot
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e ".[web]"
& $venvPython .\start_web.py

