# CodeCritique - Development environment setup (Windows PowerShell)
# Run from project root: .\scripts\setup-dev.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Host "=== CodeCritique Dev Setup ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# Python
Write-Host "--- Python ---" -ForegroundColor Yellow
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python 3.8+ required. Install from https://www.python.org/" -ForegroundColor Red
    exit 1
}

Invoke-Expression "$pythonCmd --version"
Write-Host "Installing Python dependencies..."
Invoke-Expression "$pythonCmd -m pip install --upgrade pip -q"
Invoke-Expression "$pythonCmd -m pip install -r requirements.txt -q"
Write-Host "  OK" -ForegroundColor Green
Write-Host ""

# Node (for Electron)
Write-Host "--- Node.js ---" -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVer = (node -v) -replace 'v', '' -split '\.' | Select-Object -First 1
    if ([int]$nodeVer -ge 18) {
        Write-Host "Node $(node -v) found"
        Write-Host "Installing npm dependencies..."
        npm install --silent
        Write-Host "  OK" -ForegroundColor Green
    } else {
        Write-Host "Node 18+ recommended for Electron. Current: $(node -v)"
        Write-Host "Skipping npm install. Run 'npm install' when ready."
    }
} else {
    Write-Host "Node.js not found. Optional for web-only dev."
    Write-Host "Install from https://nodejs.org/ for Electron (npm start, npm run build:win)"
}
Write-Host ""

# Data dir
if (-not (Test-Path data)) { New-Item -ItemType Directory -Path data | Out-Null }
Write-Host "Data dir: $ProjectRoot\data"
Write-Host ""

Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Run options:"
Write-Host "  Web only:     $pythonCmd app.py --dev-server"
Write-Host "  Web (prod):   $pythonCmd app.py"
Write-Host "  Electron:     npm start"
Write-Host "  Docker:       docker compose up"
Write-Host ""
