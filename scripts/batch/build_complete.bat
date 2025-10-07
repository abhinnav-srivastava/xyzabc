@echo off
title CodeCritique - Complete Build Script
echo.
echo ========================================
echo   CodeCritique - Complete Build Script
echo ========================================
echo.
echo This script will create a complete distribution package
echo with all files, folders, and dependencies included.
echo.
echo The build process includes:
echo - Portable executable with all dependencies
echo - Complete source code and documentation
echo - All configuration files and templates
echo - Installation guides and README files
echo - Distribution ZIP file for easy sharing
echo.
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Starting complete build process...
echo.

REM Run the complete build script
python scripts\py\build_complete.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for error details
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completed successfully!
echo ========================================
echo.
echo The complete distribution package has been created in the 'releases' folder.
echo.
echo You can now:
echo - Distribute the ZIP file to your team
echo - Copy the package to any computer
echo - Run the application without installation
echo.
echo Thank you for using CodeCritique!
echo.
pause
