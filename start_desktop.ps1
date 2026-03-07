$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$desktopScript = Join-Path $projectRoot "scripts\run_desktop_backend.ps1"

if (-not (Test-Path $desktopScript)) {
    throw "Cannot find desktop backend script: $desktopScript"
}

Start-Process powershell -WorkingDirectory $projectRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $desktopScript
) | Out-Null

Write-Host "Desktop mode started."
Write-Host "Application URL: http://127.0.0.1:18080"
