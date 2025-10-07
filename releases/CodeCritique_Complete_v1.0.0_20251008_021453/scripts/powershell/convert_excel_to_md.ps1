# PowerShell script to convert Excel files to Markdown format
# This script uses the existing convert_excel_to_markdown.py script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeCritique - Excel to Markdown Converter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if the conversion script exists
if (-not (Test-Path "convert_excel_to_markdown.py")) {
    Write-Host "ERROR: convert_excel_to_markdown.py not found" -ForegroundColor Red
    Write-Host "Please make sure you're running this script from the CodeCritique directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Converting all Excel files to Markdown format..." -ForegroundColor Yellow
Write-Host ""

# Run the conversion script
$result = python convert_excel_to_markdown.py --all

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Conversion failed" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Conversion completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Excel files have been converted to Markdown format in:" -ForegroundColor Green
Write-Host "- checklists\markdown\ folder" -ForegroundColor Green
Write-Host ""
Write-Host "You can now use the CodeCritique application with the updated checklists." -ForegroundColor Green
Write-Host ""

# Ask if user wants to start the application
$startApp = Read-Host "Do you want to start the CodeCritique application now? (y/n)"
if ($startApp -eq "y" -or $startApp -eq "Y") {
    Write-Host ""
    Write-Host "Starting CodeCritique application..." -ForegroundColor Yellow
    Write-Host "The application will be available at: http://localhost:5000" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
    Write-Host ""
    python app.py
} else {
    Write-Host ""
    Write-Host "You can start the application later by running: python app.py" -ForegroundColor Cyan
}

Read-Host "Press Enter to exit"
