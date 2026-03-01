# CodeReview - Development environment setup (Windows PowerShell)
# Run from project root: .\scripts\setup-dev.ps1
# Optional: .\scripts\setup-dev.ps1 -Proxy "http://proxy:8080" -Name "YourApp" -Build
# Env: $env:PIP_PROXY, $env:APP_NAME

param(
    [string]$Proxy = $env:PIP_PROXY,
    [string]$Name = $env:APP_NAME,
    [switch]$Build
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== CodeReview Dev Setup ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
if ($Proxy) { Write-Host "Pip proxy: $Proxy" }
if ($Name) { Write-Host "Restore app name to: $Name" }
if ($Build) { Write-Host "Run Electron build (build:win) after setup" }
Write-Host ""

# Restore app name (if -Name passed)
if ($Name) {
    Write-Host "--- Restore app name ---" -ForegroundColor Yellow
    $Id = ($Name -replace '\s', '').ToLower()
    $count = 0
    Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.py,*.js,*.json,*.html,*.md,*.yml,*.sh,*.ps1,*.bat -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\node_modules\\|\\\.git\\|\\dist|\\build' } | ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content -match 'CodeReview|codereview')) {
            $newContent = $content -replace 'CodeReview', $Name -replace 'codereview', $Id
            if ($newContent -ne $content) {
                Set-Content $_.FullName -Value $newContent -NoNewline
                $count++
            }
        }
    }
    Write-Host "  Updated $count files" -ForegroundColor Green
    Write-Host ""
}

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
$pipArgs = "-q"
if (-not $env:VIRTUAL_ENV) { $pipArgs = "--user -q" }
if ($Proxy) { $pipArgs = "$pipArgs --proxy $Proxy" }
Invoke-Expression "$pythonCmd -m pip install --upgrade pip $pipArgs"
Invoke-Expression "$pythonCmd -m pip install -r requirements.txt $pipArgs"
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

# Electron build (if -Build passed)
if ($Build) {
    Write-Host "--- Electron build (build:win) ---" -ForegroundColor Yellow
    if (Get-Command node -ErrorAction SilentlyContinue) {
        npm run build:win
        Write-Host "  OK" -ForegroundColor Green
    } else {
        Write-Host "Node.js required for build. Skipping." -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Run options:"
Write-Host "  Web only:     $pythonCmd app.py --dev-server"
Write-Host "  Web (prod):   $pythonCmd app.py"
Write-Host "  Electron:     npm start"
Write-Host "  Docker:       docker compose up"
Write-Host ""
