$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "fileclassifier-python-api"
$entryScript = Join-Path $backendRoot "start.ps1"

if (-not (Test-Path $entryScript)) {
    Write-Error "Cannot find startup script: $entryScript"
}

& $entryScript
