$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "fileclassifier-react-ui"

if (-not (Test-Path $frontendRoot)) {
    throw "Cannot find frontend project: $frontendRoot"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required. Please install Node.js first."
}

Set-Location $frontendRoot
if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
    npm install
}

npm run dev
