@echo off
REM CodeCritique Portable Build Script
REM Creates a standalone executable with all dependencies bundled

echo.
echo 🚀 CodeCritique Portable Build Script
echo =====================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo 📁 Project Root: %PROJECT_ROOT%
echo.

REM Check if Python is available
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)
echo ✅ Python found
echo.

REM Check if PyInstaller is available
echo 🔍 Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller not found! Installing...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ Failed to install PyInstaller!
        pause
        exit /b 1
    )
    echo ✅ PyInstaller installed successfully!
)
echo ✅ PyInstaller found
echo.

REM Run the Python build script
echo 🔨 Starting portable build process...
echo.

python "%SCRIPT_DIR%build_portable.py"

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Build completed successfully!
    echo.
    echo 📦 Distribution files created:
    echo   - CodeCritique_Portable.zip (for distribution)
    echo   - portable/ directory (for testing)
    echo.
    echo 🚀 You can now distribute the ZIP file!
    echo    Recipients just need to extract and run start.bat
    echo.
) else (
    echo.
    echo ❌ Build failed! Check the error messages above.
    echo.
)

pause
