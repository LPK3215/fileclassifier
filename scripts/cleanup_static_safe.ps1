param(
    [switch]$Force,
    [switch]$IncludeFrontendDist,
    [switch]$IncludeFrontendNodeModules,
    [switch]$IncludeRootVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Detect project root from script location:
# - If script is saved in repo root, use current dir.
# - If script is saved in repo/scripts, use parent dir.
$scriptDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$candidateA = $scriptDir
$candidateB = Split-Path -Parent $scriptDir

if (
    (Test-Path (Join-Path $candidateA "fileclassifier-python-api")) -and
    (Test-Path (Join-Path $candidateA "fileclassifier-react-ui"))
) {
    $projectRoot = (Resolve-Path -LiteralPath $candidateA).Path
}
elseif (
    (Test-Path (Join-Path $candidateB "fileclassifier-python-api")) -and
    (Test-Path (Join-Path $candidateB "fileclassifier-react-ui"))
) {
    $projectRoot = (Resolve-Path -LiteralPath $candidateB).Path
}
else {
    throw "Safety check failed: cannot detect project root from script location."
}

$projectRoot = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\', '/')

# Whitelist only: high-confidence cache targets.
$targets = @(
    "scripts/__pycache__",
    "fileclassifier-python-api/__pycache__",
    "fileclassifier-python-api/src/fileclassifier/__pycache__",
    "fileclassifier-python-api/src/fileclassifier/services/__pycache__",
    "fileclassifier-python-api/src/fileclassifier/ui/__pycache__",
    "fileclassifier-python-api/src/fileclassifier/webapi/__pycache__",
    "fileclassifier-python-api/tests/__pycache__"
)

# Optional larger/local artifacts (manual-confirm class).
if ($IncludeFrontendDist) {
    $targets += "fileclassifier-react-ui/dist"
}
if ($IncludeFrontendNodeModules) {
    $targets += "fileclassifier-react-ui/node_modules"
}
if ($IncludeRootVenv) {
    $targets += ".venv"
}

function Resolve-SafeTarget {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw "Unsafe target path: empty value."
    }
    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Unsafe target path: absolute path is not allowed ($RelativePath)."
    }
    if ($RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe target path: '..' is not allowed ($RelativePath)."
    }
    if ($RelativePath -in @(".", "/", "\")) {
        throw "Unsafe target path: root-like path is not allowed ($RelativePath)."
    }

    $joined = Join-Path $projectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $joined)) {
        return $null
    }

    $resolved = (Resolve-Path -LiteralPath $joined).Path
    $full = [System.IO.Path]::GetFullPath($resolved).TrimEnd('\', '/')

    $insideRoot = $full -eq $projectRoot -or $full.StartsWith(
        $projectRoot + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )
    if (-not $insideRoot) {
        throw "Safety check failed: target escapes project root ($RelativePath -> $full)."
    }

    if ($full -eq $projectRoot) {
        throw "Safety check failed: refusing to delete project root."
    }

    return [PSCustomObject]@{
        RelativePath = $RelativePath
        FullPath     = $full
    }
}

$existing = @()
foreach ($relative in ($targets | Select-Object -Unique)) {
    $item = Resolve-SafeTarget -RelativePath $relative
    if ($null -ne $item) {
        $existing += $item
    }
}

if (-not $existing) {
    Write-Host "No whitelisted targets found. Nothing to clean."
    exit 0
}

Write-Host "Whitelisted targets found:" -ForegroundColor Yellow
$existing | ForEach-Object { Write-Host (" - " + $_.RelativePath) }

if (-not $Force) {
    Write-Host ""
    Write-Host "Preview mode only. No files were deleted." -ForegroundColor Cyan
    Write-Host "Run with -Force to perform deletion." -ForegroundColor Cyan
    Write-Host "Optional switches: -IncludeFrontendDist -IncludeFrontendNodeModules -IncludeRootVenv"
    exit 0
}

foreach ($item in $existing) {
    Remove-Item -LiteralPath $item.FullPath -Recurse -Force
    Write-Host ("Deleted: " + $item.RelativePath)
}

Write-Host "Cleanup completed." -ForegroundColor Green
