# CodeCritique Start Script for PowerShell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting CodeCritique" -ForegroundColor Cyan
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
Write-Host "Starting CodeCritique server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "The application will be available at: http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the application
python app.py
