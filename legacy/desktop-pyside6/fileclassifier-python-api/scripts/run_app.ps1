$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$entryScript = Join-Path $projectRoot "start.ps1"

if (-not (Test-Path $entryScript)) {
    Write-Error "Cannot find startup script: $entryScript"
}

& $entryScript
