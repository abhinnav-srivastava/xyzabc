# CodeCritique Setup Script for PowerShell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeCritique Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
try {
    python -m venv .venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "Using advanced proxy detection..." -ForegroundColor Yellow

try {
    python proxy_setup.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "WARNING: Failed to install dependencies automatically" -ForegroundColor Yellow
        Write-Host "You can continue with setup and install dependencies manually later" -ForegroundColor Yellow
        Write-Host ""
        $continue = Read-Host "Continue with setup? (y/n)"
        if ($continue -notmatch "^[yY]") {
            Write-Host "Setup cancelled by user" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Host "Skipping dependency installation..." -ForegroundColor Yellow
        Write-Host "You can install dependencies later by running:" -ForegroundColor White
        Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "  pip install -r requirements.txt" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host ""
    Write-Host "WARNING: Failed to run proxy setup script" -ForegroundColor Yellow
    Write-Host "You can continue with setup and install dependencies manually later" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue with setup? (y/n)"
    if ($continue -notmatch "^[yY]") {
        Write-Host "Setup cancelled by user" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Skipping dependency installation..." -ForegroundColor Yellow
    Write-Host "You can install dependencies later by running:" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
}

Write-Host ""

# Convert Excel files
Write-Host "Converting Excel files to Markdown..." -ForegroundColor Yellow
try {
    python convert_excel_to_markdown.py --all
    Write-Host "Excel files converted successfully!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Failed to convert Excel files (this is optional)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start CodeCritique:" -ForegroundColor White
Write-Host "1. Run: .\start.ps1" -ForegroundColor White
Write-Host "2. Or manually: .\.venv\Scripts\Activate.ps1; python app.py" -ForegroundColor White
Write-Host "3. Open browser to: http://localhost:5000" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
