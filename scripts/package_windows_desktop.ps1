param(
    [ValidateSet("onedir", "onefile")]
    [string]$Mode = "onefile",
    [ValidateSet("console", "windowed")]
    [string]$UiMode = "console"
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This script is for Windows only."
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$packagingConfigPath = Join-Path $PSScriptRoot "package_windows_desktop.config.json"

if (-not (Test-Path $packagingConfigPath)) {
    throw "Missing packaging config: $packagingConfigPath"
}

$packagingConfig = Get-Content -Raw -Path $packagingConfigPath | ConvertFrom-Json -Depth 30

function Resolve-ProjectPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return Join-Path $projectRoot $RelativePath
}

function Format-CommandString {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $parts = @($Executable) + $Arguments
    $escaped = foreach ($part in $parts) {
        if ($part -match '\s|"') {
            '"' + ($part -replace '"', '\"') + '"'
        }
        else {
            $part
        }
    }
    return ($escaped -join " ")
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    $commandText = Format-CommandString -Executable $Executable -Arguments $Arguments
    Write-Host ">> $commandText"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code: $LASTEXITCODE)."
    }
}

$backendRoot = Resolve-ProjectPath $packagingConfig.backend_dir
$frontendRoot = Resolve-ProjectPath $packagingConfig.frontend_dir
$distRoot = Resolve-ProjectPath $packagingConfig.dist_dir
$buildRoot = Resolve-ProjectPath $packagingConfig.build_dir
$specRoot = Resolve-ProjectPath $packagingConfig.spec_dir
$backendVenv = Join-Path $backendRoot $packagingConfig.venv_dir
$venvPython = Join-Path $backendVenv $packagingConfig.venv_python_relative
$systemPython = [string]($packagingConfig.system_python)
$appName = [string]($packagingConfig.app_name)

if (-not (Test-Path $backendRoot)) {
    throw "Cannot find backend project: $backendRoot"
}
if (-not (Test-Path $frontendRoot)) {
    throw "Cannot find frontend project: $frontendRoot"
}
if (-not (Test-Path $specRoot)) {
    throw "Cannot find spec output directory: $specRoot"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required. Please install Node.js first."
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating backend virtual environment..."
    Invoke-LoggedCommand `
        -Executable $systemPython `
        -Arguments @("-m", "venv", $backendVenv) `
        -FailureMessage "Failed to create backend venv"
}

Write-Host "Building frontend production assets..."
Push-Location $frontendRoot
try {
    if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
        Invoke-LoggedCommand -Executable "npm" -Arguments @("install") -FailureMessage "npm install failed"
    }
    Invoke-LoggedCommand -Executable "npm" -Arguments @("run", "build") -FailureMessage "npm run build failed"
}
finally {
    Pop-Location
}

$frontendDist = Join-Path $frontendRoot "dist"
if (-not (Test-Path (Join-Path $frontendDist "index.html"))) {
    throw "Frontend dist output is missing: $frontendDist"
}

Write-Host "Installing backend runtime dependencies..."
Push-Location $backendRoot
try {
    Invoke-LoggedCommand `
        -Executable $venvPython `
        -Arguments @("-m", "pip", "install", "--upgrade", "pip") `
        -FailureMessage "Failed to upgrade pip"

    Invoke-LoggedCommand `
        -Executable $venvPython `
        -Arguments @("-m", "pip", "install", "-e", ([string]($packagingConfig.backend_editable_dependency))) `
        -FailureMessage "Failed to install backend dependencies"

    $hasPyInstaller = & $venvPython -c "import importlib.util; print('1' if importlib.util.find_spec('PyInstaller') else '0')"
    if ($hasPyInstaller.Trim() -ne "1") {
        Invoke-LoggedCommand `
            -Executable $venvPython `
            -Arguments @("-m", "pip", "install", ([string]($packagingConfig.pyinstaller_version_spec))) `
            -FailureMessage "Failed to install PyInstaller"
    }

    $addDataFrontend = "$frontendDist;frontend_dist"
    $addDataBackend = (Join-Path $backendRoot "data") + ";data"

    $buildArgs = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", $appName,
        "--distpath", $distRoot,
        "--workpath", $buildRoot,
        "--specpath", $specRoot,
        "--paths", (Join-Path $backendRoot "src"),
        "--collect-submodules", "fileclassifier",
        "--add-data", $addDataFrontend,
        "--add-data", $addDataBackend
    )

    if ($UiMode -eq "windowed") {
        $buildArgs += "--windowed"
    }
    else {
        $buildArgs += "--console"
    }

    if ($Mode -eq "onefile") {
        $buildArgs += "--onefile"
    }

    $targetOutput = if ($Mode -eq "onefile") {
        Join-Path $distRoot "$appName.exe"
    }
    else {
        Join-Path $distRoot $appName
    }

    if (Test-Path $targetOutput) {
        try {
            Remove-Item -Path $targetOutput -Recurse -Force -ErrorAction Stop
        }
        catch {
            throw (
                "Cannot overwrite existing output: $targetOutput. " +
                "Please close any running FileClassifier app and retry. " +
                "Detail: $($_.Exception.Message)"
            )
        }
    }

    $entryScript = Join-Path $backendRoot ([string]($packagingConfig.entry_script))
    if (-not (Test-Path $entryScript)) {
        throw "Cannot find backend entry script: $entryScript"
    }
    $buildArgs += $entryScript

    Write-Host "Packaging desktop executable ($Mode, $UiMode)..."
    Invoke-LoggedCommand `
        -Executable $venvPython `
        -Arguments $buildArgs `
        -FailureMessage "PyInstaller build failed"
}
finally {
    Pop-Location
}

$exePath = if ($Mode -eq "onefile") {
    Join-Path $distRoot "$appName.exe"
}
else {
    Join-Path $distRoot "$appName\$appName.exe"
}

if (-not (Test-Path $exePath)) {
    throw "Build finished but executable not found: $exePath"
}

$launchDir = Split-Path -Parent $exePath
$configOutput = Join-Path $launchDir ([string]$packagingConfig.desktop_config_filename)
$configExampleOutput = Join-Path $launchDir ([string]$packagingConfig.desktop_config_example_filename)
$desktopConfigTemplate = $packagingConfig.desktop_config_template | ConvertTo-Json -Depth 20

if (-not (Test-Path $configOutput)) {
    Set-Content -Path $configOutput -Value $desktopConfigTemplate -Encoding UTF8
}
Set-Content -Path $configExampleOutput -Value $desktopConfigTemplate -Encoding UTF8

Write-Host ""
Write-Host "Build succeeded."
Write-Host "Double-click to launch:"
Write-Host $exePath
Write-Host "UI mode: $UiMode"
Write-Host "Config file: $configOutput"
Write-Host "Packaging config source: $packagingConfigPath"
