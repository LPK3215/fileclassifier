param(
    [ValidateSet("onedir", "onefile")]
    [string]$Mode = "onedir"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$bootstrapScript = Join-Path $projectRoot "scripts\bootstrap_venv.ps1"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$appName = "FileClassifier"

if (-not (Test-Path $venvPython)) {
    if (-not (Test-Path $bootstrapScript)) {
        Write-Error "Cannot find bootstrap script: $bootstrapScript"
    }
    & $bootstrapScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to bootstrap local venv (exit code: $LASTEXITCODE)."
    }
}

$hasPyInstaller = & $venvPython -c "import importlib.util; print('1' if importlib.util.find_spec('PyInstaller') else '0')"
if ($hasPyInstaller.Trim() -ne "1") {
    & $venvPython -m pip install "pyinstaller>=6.13,<7"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Default PyPI install failed. Trying Tsinghua mirror..."
        & $venvPython -m pip install "pyinstaller>=6.13,<7" `
            -i "https://pypi.tuna.tsinghua.edu.cn/simple" `
            --trusted-host "pypi.tuna.tsinghua.edu.cn"
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error (
            "Failed to install PyInstaller (exit code: $LASTEXITCODE). " +
            "Please check your network/PyPI access and run the script again."
        )
    }
}

$buildArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", $appName,
    "--distpath", (Join-Path $projectRoot "dist"),
    "--workpath", (Join-Path $projectRoot "build"),
    "--specpath", $projectRoot,
    "--paths", (Join-Path $projectRoot "src"),
    "--add-data", "data/sample_records.xlsx:data",
    "--add-data", "src/fileclassifier/assets:assets"
)

if ($Mode -eq "onefile") {
    $buildArgs += "--onefile"
}

$buildArgs += (Join-Path $projectRoot "src\fileclassifier\main.py")

& $venvPython @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed (exit code: $LASTEXITCODE)."
}

$exePath = if ($Mode -eq "onefile") {
    Join-Path $projectRoot "dist\$appName.exe"
} else {
    Join-Path $projectRoot "dist\$appName\$appName.exe"
}

if (-not (Test-Path $exePath)) {
    Write-Error "Build finished but executable not found: $exePath"
}

Write-Host ""
Write-Host "Build succeeded."
Write-Host "Double-click executable:"
Write-Host $exePath
