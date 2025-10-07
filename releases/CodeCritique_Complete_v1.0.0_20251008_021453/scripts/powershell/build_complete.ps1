# CodeCritique - Complete Build Script (PowerShell)
# Creates a complete distribution package with all files and folders

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CodeCritique - Complete Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will create a complete distribution package" -ForegroundColor Yellow
Write-Host "with all files, folders, and dependencies included." -ForegroundColor Yellow
Write-Host ""
Write-Host "The build process includes:" -ForegroundColor Green
Write-Host "- Portable executable with all dependencies" -ForegroundColor White
Write-Host "- Complete source code and documentation" -ForegroundColor White
Write-Host "- All configuration files and templates" -ForegroundColor White
Write-Host "- Installation guides and README files" -ForegroundColor White
Write-Host "- Distribution ZIP file for easy sharing" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting complete build process..." -ForegroundColor Yellow
Write-Host ""

# Run the complete build script
try {
    python scripts\py\build_complete.py
    
    if ($LASTEXITCODE -ne 0) {
        throw "Build script failed"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   Build completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The complete distribution package has been created in the 'releases' folder." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Cyan
    Write-Host "- Distribute the ZIP file to your team" -ForegroundColor White
    Write-Host "- Copy the package to any computer" -ForegroundColor White
    Write-Host "- Run the application without installation" -ForegroundColor White
    Write-Host ""
    Write-Host "Thank you for using CodeCritique!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Write-Host "Check the output above for error details" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"
