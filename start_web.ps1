$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendScript = Join-Path $projectRoot "scripts\run_web_backend.ps1"
$frontendScript = Join-Path $projectRoot "scripts\run_web_frontend.ps1"
$runtimeStateDir = Join-Path $projectRoot ".runtime\web-stack"
$runtimeStatePath = Join-Path $runtimeStateDir "processes.json"

if (-not (Test-Path $backendScript)) {
    throw "Cannot find backend script: $backendScript"
}
if (-not (Test-Path $frontendScript)) {
    throw "Cannot find frontend script: $frontendScript"
}

$backendProcess = Start-Process powershell -PassThru -WorkingDirectory $projectRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $backendScript
)

$frontendProcess = Start-Process powershell -PassThru -WorkingDirectory $projectRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $frontendScript
)

New-Item -ItemType Directory -Path $runtimeStateDir -Force | Out-Null

$processState = [ordered]@{
    created_at = (Get-Date).ToString("o")
    backend = [ordered]@{
        pid = $backendProcess.Id
        started_at = $backendProcess.StartTime.ToString("o")
        script = $backendScript
    }
    frontend = [ordered]@{
        pid = $frontendProcess.Id
        started_at = $frontendProcess.StartTime.ToString("o")
        script = $frontendScript
    }
}

$processState | ConvertTo-Json -Depth 8 | Set-Content -Path $runtimeStatePath -Encoding UTF8

Write-Host "Web stack started."
Write-Host "Backend API: http://127.0.0.1:8000/api/health"
Write-Host "Frontend UI: http://127.0.0.1:5173"
Write-Host "Process state file: $runtimeStatePath"
Write-Host "Stop command: .\stop_web.ps1"
