$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "fileclassifier-python-api"
$venvPath = Join-Path $backendRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$systemPython = "python"

if (-not (Test-Path $backendRoot)) {
    throw "Cannot find backend project: $backendRoot"
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv for backend..."
    & $systemPython -m venv $venvPath
}

Set-Location $backendRoot
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e ".[web]"
& $venvPython .\start_web.py
