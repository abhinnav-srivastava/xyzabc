# CodeCritique - Comprehensive Build Script (PowerShell)
# Builds both portable executable and desktop app distributions

param(
    [switch]$PortableOnly,
    [switch]$DesktopOnly,
    [switch]$Clean,
    [switch]$Help
)

if ($Help) {
    Write-Host "CodeCritique Build Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\build_all.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -PortableOnly    Build only portable version"
    Write-Host "  -DesktopOnly     Build only desktop version"
    Write-Host "  -Clean           Clean build directories only"
    Write-Host "  -Help            Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\build_all.ps1                    # Build both versions"
    Write-Host "  .\build_all.ps1 -PortableOnly       # Build only portable"
    Write-Host "  .\build_all.ps1 -DesktopOnly        # Build only desktop"
    Write-Host "  .\build_all.ps1 -Clean             # Clean directories"
    exit 0
}

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$SuccessColor = "Green"
$ErrorColor = "Red"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $InfoColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $WarningColor
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "🚀 CodeCritique Build Script" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

try {
    # Change to project root
    Set-Location $ProjectRoot
    
    if ($Clean) {
        Write-Info "Cleaning build directories..."
        
        $DirsToClean = @("build", "dist", "portable", "releases")
        foreach ($Dir in $DirsToClean) {
            if (Test-Path $Dir) {
                Remove-Item -Recurse -Force $Dir
                Write-Success "Cleaned $Dir"
            }
        }
        
        Write-Success "Build directories cleaned!"
        exit 0
    }
    
    # Check for conflicting options
    if ($PortableOnly -and $DesktopOnly) {
        Write-Error "Cannot specify both -PortableOnly and -DesktopOnly"
        exit 1
    }
    
    # Build process
    $BuildArgs = @()
    if ($PortableOnly) { $BuildArgs += "--portable-only" }
    if ($DesktopOnly) { $BuildArgs += "--desktop-only" }
    
    Write-Info "Starting build process..."
    Write-Info "Arguments: $($BuildArgs -join ' ')"
    
    # Run the Python build script
    $PythonScript = Join-Path $ProjectRoot "scripts\py\build_all.py"
    
    if (-not (Test-Path $PythonScript)) {
        Write-Error "Build script not found: $PythonScript"
        exit 1
    }
    
    # Check if Python is available
    try {
        $PythonVersion = python --version 2>&1
        Write-Info "Using Python: $PythonVersion"
    } catch {
        Write-Error "Python is not installed or not in PATH"
        Write-Info "Please install Python from https://python.org"
        exit 1
    }
    
    # Run the build
    $BuildCommand = "python `"$PythonScript`" $($BuildArgs -join ' ')"
    Write-Info "Running: $BuildCommand"
    
    Invoke-Expression $BuildCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build completed successfully!"
        
        # Show release packages
        $ReleasesDir = Join-Path $ProjectRoot "releases"
        if (Test-Path $ReleasesDir) {
            Write-Info "Release packages created:"
            Get-ChildItem $ReleasesDir -File | ForEach-Object {
                Write-Host "  📦 $($_.Name)" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        Write-Host "🎉 All builds completed successfully!" -ForegroundColor Green
        Write-Host "📦 Release packages: $ReleasesDir" -ForegroundColor Cyan
        Write-Host "🚀 You can now distribute the release packages!" -ForegroundColor Yellow
        
    } else {
        Write-Error "Build failed with exit code: $LASTEXITCODE"
        exit 1
    }
    
} catch {
    Write-Error "Build script failed: $($_.Exception.Message)"
    exit 1
} finally {
    # Return to original directory
    Set-Location $PWD
}

