$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$python = "python"

if (-not (Test-Path $venvPath)) {
    & $python -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e ".[dev]"
