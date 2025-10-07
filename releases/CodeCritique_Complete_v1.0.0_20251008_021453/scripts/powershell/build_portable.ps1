# CodeCritique Portable Build Script
# Creates a standalone executable with all dependencies bundled

param(
    [switch]$Clean,
    [switch]$Help
)

if ($Help) {
    Write-Host "CodeCritique Portable Build Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\build_portable.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Clean    Clean build directories before building" -ForegroundColor White
    Write-Host "  -Help     Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\build_portable.ps1              # Build portable version" -ForegroundColor White
    Write-Host "  .\build_portable.ps1 -Clean       # Clean and build" -ForegroundColor White
    exit 0
}

Write-Host "🚀 CodeCritique Portable Build Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if PyInstaller is available
Write-Host "🔍 Checking PyInstaller..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = python -m PyInstaller --version 2>&1
    Write-Host "✅ PyInstaller found: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ PyInstaller not found! Installing..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install PyInstaller!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ PyInstaller installed successfully!" -ForegroundColor Green
}

# Clean build directories if requested
if ($Clean) {
    Write-Host "🧹 Cleaning build directories..." -ForegroundColor Yellow
    $BuildDirs = @("build", "dist", "portable")
    foreach ($Dir in $BuildDirs) {
        $DirPath = Join-Path $ProjectRoot $Dir
        if (Test-Path $DirPath) {
            Remove-Item -Recurse -Force $DirPath
            Write-Host "✅ Cleaned $Dir" -ForegroundColor Green
        }
    }
    Write-Host ""
}

# Run the Python build script
Write-Host "🔨 Starting portable build process..." -ForegroundColor Yellow
Write-Host ""

$BuildScript = Join-Path $ScriptDir "build_portable.py"
python $BuildScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Distribution files created:" -ForegroundColor Cyan
    Write-Host "  - CodeCritique_Portable.zip (for distribution)" -ForegroundColor White
    Write-Host "  - portable/ directory (for testing)" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 You can now distribute the ZIP file!" -ForegroundColor Green
    Write-Host "   Recipients just need to extract and run start.bat" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Build failed! Check the error messages above." -ForegroundColor Red
    exit 1
}


