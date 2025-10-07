@echo off
REM CodeCritique - Comprehensive Build Script (Batch)
REM Builds both portable executable and desktop app distributions

setlocal enabledelayedexpansion

REM Colors (using ANSI escape codes)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "CYAN=[36m"
set "NC=[0m"

REM Parse command line arguments
set "PORTABLE_ONLY=false"
set "DESKTOP_ONLY=false"
set "CLEAN=false"
set "HELP=false"

:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="--portable-only" (
    set "PORTABLE_ONLY=true"
    shift
    goto :parse_args
)
if "%~1"=="--desktop-only" (
    set "DESKTOP_ONLY=true"
    shift
    goto :parse_args
)
if "%~1"=="--clean" (
    set "CLEAN=true"
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    set "HELP=true"
    shift
    goto :parse_args
)
if "%~1"=="-h" (
    set "HELP=true"
    shift
    goto :parse_args
)
echo %CYAN%Unknown option: %~1%NC%
exit /b 1

:args_done

REM Show help
if "%HELP%"=="true" (
    echo %GREEN%CodeCritique Build Script%NC%
    echo.
    echo %YELLOW%Usage: build_all.bat [options]%NC%
    echo.
    echo %CYAN%Options:%NC%
    echo   --portable-only    Build only portable version
    echo   --desktop-only     Build only desktop version
    echo   --clean           Clean build directories only
    echo   --help, -h         Show this help message
    echo.
    echo %YELLOW%Examples:%NC%
    echo   build_all.bat                    # Build both versions
    echo   build_all.bat --portable-only    # Build only portable
    echo   build_all.bat --desktop-only     # Build only desktop
    echo   build_all.bat --clean           # Clean directories
    exit /b 0
)

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo %GREEN%🚀 CodeCritique Build Script%NC%
echo %BLUE%Project Root: %PROJECT_ROOT%%NC%

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Check for conflicting options
if "%PORTABLE_ONLY%"=="true" if "%DESKTOP_ONLY%"=="true" (
    echo %RED%❌ Cannot specify both --portable-only and --desktop-only%NC%
    exit /b 1
)

REM Clean directories if requested
if "%CLEAN%"=="true" (
    echo %CYAN%ℹ️  Cleaning build directories...%NC%
    
    set "DIRS_TO_CLEAN=build dist portable releases"
    for %%d in (%DIRS_TO_CLEAN%) do (
        if exist "%%d" (
            rmdir /s /q "%%d"
            echo %GREEN%✅ Cleaned %%d%NC%
        )
    )
    
    echo %GREEN%✅ Build directories cleaned!%NC%
    exit /b 0
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Python is not installed or not in PATH%NC%
    echo %CYAN%ℹ️  Please install Python from https://python.org%NC%
    exit /b 1
)

REM Get Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo %CYAN%ℹ️  Using Python: %PYTHON_VERSION%%NC%

REM Build process
set "BUILD_ARGS="
if "%PORTABLE_ONLY%"=="true" set "BUILD_ARGS=%BUILD_ARGS% --portable-only"
if "%DESKTOP_ONLY%"=="true" set "BUILD_ARGS=%BUILD_ARGS% --desktop-only"

echo %CYAN%ℹ️  Starting build process...%NC%
echo %CYAN%ℹ️  Arguments: %BUILD_ARGS%%NC%

REM Run the Python build script
set "PYTHON_SCRIPT=%PROJECT_ROOT%\scripts\py\build_all.py"

if not exist "%PYTHON_SCRIPT%" (
    echo %RED%❌ Build script not found: %PYTHON_SCRIPT%%NC%
    exit /b 1
)

REM Run the build
set "BUILD_COMMAND=python \"%PYTHON_SCRIPT%\" %BUILD_ARGS%"
echo %CYAN%ℹ️  Running: %BUILD_COMMAND%%NC%

%BUILD_COMMAND%
if errorlevel 1 (
    echo %RED%❌ Build failed with exit code: %errorlevel%%NC%
    exit /b 1
)

echo %GREEN%✅ Build completed successfully!%NC%

REM Show release packages
set "RELEASES_DIR=%PROJECT_ROOT%\releases"
if exist "%RELEASES_DIR%" (
    echo %CYAN%ℹ️  Release packages created:%NC%
    for %%f in ("%RELEASES_DIR%\*") do (
        echo   %BLUE%📦 %%~nxf%NC%
    )
)

echo.
echo %GREEN%🎉 All builds completed successfully!%NC%
echo %CYAN%📦 Release packages: %RELEASES_DIR%%NC%
echo %YELLOW%🚀 You can now distribute the release packages!%NC%

