# CodeCritique - Manual Dependency Installation Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeCritique - Manual Dependency Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Virtual environment not found" -ForegroundColor Red
    Write-Host "Please run setup.ps1 first" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "Installing dependencies with advanced proxy detection..." -ForegroundColor Yellow
try {
    python proxy_setup.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Manual installation options:" -ForegroundColor Yellow
        Write-Host "1. Try without proxy: pip install -r requirements.txt" -ForegroundColor White
        Write-Host "2. Try with specific proxy: pip install --proxy http://your-proxy:port -r requirements.txt" -ForegroundColor White
        Write-Host "3. Try with trusted hosts: pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    Write-Host "You can now run CodeCritique using start.ps1" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check your internet connection and proxy settings" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
