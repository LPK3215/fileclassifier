$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$runtimeStatePath = Join-Path $projectRoot ".runtime\web-stack\processes.json"

if (-not (Test-Path $runtimeStatePath)) {
    Write-Host "No web stack state file found. Nothing to stop."
    Write-Host "Expected state file: $runtimeStatePath"
    exit 0
}

$stateRaw = Get-Content -Raw -Path $runtimeStatePath
$state = $stateRaw | ConvertFrom-Json -Depth 8
$stopped = @()
$skipped = @()

function Stop-TrackedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$Entry
    )

    if (-not $Entry -or -not $Entry.pid) {
        $script:skipped += "$Name (missing pid)"
        return
    }

    $pid = [int]$Entry.pid
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if (-not $proc) {
        $script:skipped += "$Name (pid $pid not running)"
        return
    }

    $expectedStart = $null
    if ($Entry.started_at) {
        try {
            $expectedStart = [DateTime]::Parse([string]$Entry.started_at).ToUniversalTime()
        }
        catch {
            $expectedStart = $null
        }
    }

    if ($expectedStart) {
        try {
            $actualStart = $proc.StartTime.ToUniversalTime()
            if ([Math]::Abs(($actualStart - $expectedStart).TotalSeconds) -gt 2) {
                $script:skipped += "$Name (pid reused, skipped)"
                return
            }
        }
        catch {
            # Ignore start-time check failures and stop process directly.
        }
    }

    Stop-Process -Id $pid -Force -ErrorAction Stop
    $script:stopped += "$Name (pid $pid)"
}

Stop-TrackedProcess -Name "backend-shell" -Entry $state.backend
Stop-TrackedProcess -Name "frontend-shell" -Entry $state.frontend

Remove-Item -Path $runtimeStatePath -Force -ErrorAction SilentlyContinue

if ($stopped.Count -gt 0) {
    Write-Host "Stopped processes:"
    $stopped | ForEach-Object { Write-Host " - $_" }
}
else {
    Write-Host "No running tracked processes were stopped."
}

if ($skipped.Count -gt 0) {
    Write-Host "Skipped entries:"
    $skipped | ForEach-Object { Write-Host " - $_" }
}
