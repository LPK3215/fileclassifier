$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "fileclassifier-python-api"
$frontendRoot = Join-Path $projectRoot "fileclassifier-react-ui"
$frontendDistIndex = Join-Path $frontendRoot "dist\index.html"
$venvPath = Join-Path $backendRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$systemPython = "python"

if (-not (Test-Path $backendRoot)) {
    throw "Cannot find backend project: $backendRoot"
}
if (-not (Test-Path $frontendRoot)) {
    throw "Cannot find frontend project: $frontendRoot"
}

if (-not (Test-Path $frontendDistIndex)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm is required to build frontend assets. Please install Node.js."
    }
    Set-Location $frontendRoot
    if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
        npm install
    }
    npm run build
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating backend virtual environment..."
    & $systemPython -m venv $venvPath
}

Set-Location $backendRoot
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e ".[web]"
& $venvPython .\start_desktop.py
