# CodeReview - Development environment setup (Windows PowerShell)
# Run from project root: .\scripts\setup-dev.ps1
# Optional: .\scripts\setup-dev.ps1 -Proxy "http://proxy:8080" -Name "YourApp" -Build -Venv
# With auth (no encoding needed): .\scripts\setup-dev.ps1 -Proxy "http://proxy:8080" -ProxyUser "user" -ProxyPass "sr!n@v9914"
# Note: Use -Build, -Venv (PowerShell style), not --build, --venv
# Env: $env:PIP_PROXY, $env:PIP_PROXY_USER, $env:PIP_PROXY_PASS, $env:APP_NAME

param(
    [string]$Proxy = $env:PIP_PROXY,
    [string]$ProxyUser = $env:PIP_PROXY_USER,
    [string]$ProxyPass = $env:PIP_PROXY_PASS,
    [string]$Name = $env:APP_NAME,
    [switch]$Build,
    [switch]$Venv
)

# Fix: --build/--venv wrongly captured as Proxy (env or typo)
if ($Proxy -in '--build','-build','build') { $Proxy = $null; $Build = $true }
if ($Proxy -in '--venv','-venv','venv') { $Proxy = $null; $Venv = $true }

# Prompt for proxy settings if not provided (interactive)
if (-not $Proxy) { $Proxy = Read-Host "Proxy URL (e.g. http://proxy:8080) [Enter to skip]" }
if ($Proxy -and -not $ProxyUser) { $ProxyUser = Read-Host "Proxy username [Enter to skip]" }
if ($Proxy -and $ProxyUser -and -not $ProxyPass) {
    $sec = Read-Host "Proxy password [Enter to skip]" -AsSecureString
    $ProxyPass = if ($sec.Length -gt 0) { [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)) } else { "" }
}

# Prompt for Name, Venv, Build if not provided (interactive)
if (-not $Name) { $Name = Read-Host "App name to restore (e.g. CodeCritique) [Enter to skip]" }
if (-not $Venv) { $r = Read-Host "Create virtual environment (.venv)? [y/N]"; $Venv = ($r -match '^[yY]') }
if (-not $Build) { $r = Read-Host "Run Electron build after setup? [y/N]"; $Build = ($r -match '^[yY]') }

# Build proxy URL with auth: Proxy + ProxyUser + ProxyPass (auto URL-encodes special chars)
if ($Proxy -and $ProxyUser -and $ProxyPass) {
    $encUser = [Uri]::EscapeDataString($ProxyUser)
    $encPass = [Uri]::EscapeDataString($ProxyPass)
    if ($Proxy -match '^(https?)://(.+)$') {
        $Proxy = "$($Matches[1])://${encUser}:${encPass}@$($Matches[2])"
    }
}

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Helper: run a block; on failure log and continue (do not exit)
function Invoke-Step {
    param([string]$Name, [scriptblock]$Block)
    try {
        & $Block
    } catch {
        Write-Host "  $Name failed (continuing)" -ForegroundColor Yellow
        Write-Host "  $_" -ForegroundColor Gray
    }
}

Write-Host "=== CodeReview Dev Setup ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
if ($Proxy) {
    $displayProxy = if ($Proxy -match '^([^:]+://)[^:]+:[^@]+@(.+)$') { $Matches[1] + '***:***@' + $Matches[2] } else { $Proxy }
    Write-Host "Pip proxy: $displayProxy"
}
if ($Name) { Write-Host "Restore app name to: $Name" }
if ($Build) { Write-Host "Run Electron build (build:win) after setup" }
if ($Venv) { Write-Host "Create venv (.venv) for dependencies" }
Write-Host ""

# Restore app name (if -Name passed)
if ($Name) {
    Write-Host "--- Restore app name ---" -ForegroundColor Yellow
    Invoke-Step "Restore app name" {
        $Id = ($Name -replace '\s', '').ToLower()
        $count = 0
        Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.py,*.js,*.json,*.html,*.md,*.yml,*.sh,*.ps1,*.bat,*.spec -ErrorAction SilentlyContinue |
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
        # Ensure package.json "name" is valid for npm/electron-builder (lowercase, no spaces)
        $pkgPath = Join-Path $ProjectRoot "package.json"
        if (Test-Path $pkgPath) {
            try {
                $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
                $validName = ($pkg.name -replace '[^a-z0-9\-]', '').ToLower()
                if ([string]::IsNullOrWhiteSpace($validName)) { $validName = $Id }
                if ($pkg.name -ne $validName) {
                    $pkg.name = $validName
                    $pkg | ConvertTo-Json -Depth 20 | Set-Content $pkgPath -NoNewline
                    $count++
                }
            } catch { }
        }
        Write-Host "  Updated $count files" -ForegroundColor Green
    } | Out-Null
    Write-Host ""
}

# Python - resolve to executable path for reliable invocation (paths with spaces/parentheses)
Write-Host "--- Python ---" -ForegroundColor Yellow
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = (Get-Command python).Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pyExe = (py -3 -c "import sys; print(sys.executable)" 2>$null)
    if ($pyExe) { $pythonCmd = $pyExe.Trim() }
    else { $pythonCmd = (Get-Command py).Source; $script:pythonLauncher = @("-3") }
}
$pythonLauncher = if (Get-Variable -Name pythonLauncher -Scope Script -ErrorAction SilentlyContinue) { $script:pythonLauncher } else { @() }

if (-not $pythonCmd) {
    Write-Host "ERROR: Python 3.8+ required. Install from https://www.python.org/" -ForegroundColor Red
    exit 1
}

& $pythonCmd @pythonLauncher --version 2>&1 | Out-Null

# Create venv if -Venv passed
if ($Venv) {
    $venvPath = Join-Path $ProjectRoot ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating venv at .venv..."
        try {
            & $pythonCmd @pythonLauncher -m venv $venvPath 2>&1 | Out-Null
            Write-Host "  Created" -ForegroundColor Green
        } catch {
            Write-Host "  Venv creation failed (continuing)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Venv .venv exists"
    }
    $pythonCmd = Join-Path $venvPath "Scripts\python.exe"
    $pythonLauncher = @()
}

Write-Host "Installing Python dependencies..."
$pipArgs = @("-q")
if (-not $Venv -and -not $env:VIRTUAL_ENV) { $pipArgs = @("--user", "-q") }
if ($Proxy) { $pipArgs += "--proxy"; $pipArgs += $Proxy }
try {
    & $pythonCmd @pythonLauncher -m pip install --upgrade pip @pipArgs 2>&1 | Out-Null
    & $pythonCmd @pythonLauncher -m pip install -r requirements.txt @pipArgs 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "  OK" -ForegroundColor Green } else {
        Write-Host "  pip install failed (continuing)" -ForegroundColor Yellow
        Write-Host "  If pip failed, checklist migration will also fail. Run: pip install -r requirements.txt" -ForegroundColor Gray
    }
} catch {
    Write-Host "  pip install failed (continuing). Run: pip install -r requirements.txt" -ForegroundColor Yellow
}
if ($Venv) {
    Write-Host "Activate venv: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
}
Write-Host ""

# Checklist migration (Excel -> Markdown)
Write-Host "--- Checklist migration (Excel -> Markdown) ---" -ForegroundColor Yellow
$migrateScript = Join-Path $ProjectRoot "scripts\py\auto_update_checklists.py"
if (Test-Path $migrateScript) {
    try {
        & $pythonCmd @pythonLauncher $migrateScript 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK" -ForegroundColor Green
        } else {
            Write-Host "  Checklist migration failed (continuing)" -ForegroundColor Yellow
            Write-Host "  If pip install failed above, run: pip install pandas openpyxl" -ForegroundColor Gray
            Write-Host "  Then: python scripts/py/auto_update_checklists.py" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Checklist migration failed (continuing)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  auto_update_checklists.py not found, skipping" -ForegroundColor Gray
}
Write-Host ""

# Node (for Electron)
Write-Host "--- Node.js ---" -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVer = (node -v) -replace 'v', '' -split '\.' | Select-Object -First 1
    if ([int]$nodeVer -ge 18) {
        Write-Host "Node $(node -v) found"
        Write-Host "Installing npm dependencies..."
        npm install --silent 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "  OK" -ForegroundColor Green } else { Write-Host "  npm install failed (continuing)" -ForegroundColor Yellow }
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
if (-not (Test-Path data)) { New-Item -ItemType Directory -Path data -ErrorAction SilentlyContinue | Out-Null }
Write-Host "Data dir: $ProjectRoot\data"
Write-Host ""

# Electron build (if -Build passed) - resilient: setup completes even if build fails
if ($Build) {
    Write-Host "--- Electron build (build:win) ---" -ForegroundColor Yellow
    if (Get-Command node -ErrorAction SilentlyContinue) {
        # npm does not throw; check $LASTEXITCODE explicitly
        npm run build:win
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Electron build failed (setup continues)" -ForegroundColor Yellow
            Write-Host "  Run 'npm run build:win' manually later." -ForegroundColor Gray
            Write-Host "  Or 'npm run build:win:pyonly' to build just the PyInstaller exe (skip Electron)." -ForegroundColor Gray
            Write-Host "  Common causes: Python 3.9+, npm install, proxy/network, disk space." -ForegroundColor Gray
        } else {
            Write-Host "  OK" -ForegroundColor Green
        }
    } else {
        Write-Host "Node.js required for build. Skipping." -ForegroundColor Yellow
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
