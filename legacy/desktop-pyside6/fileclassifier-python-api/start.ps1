$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$systemPython = "python"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating local .venv and installing runtime dependencies..."
    & $systemPython -m venv $venvPath
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -e "$projectRoot"
}

& $venvPython -m fileclassifier
