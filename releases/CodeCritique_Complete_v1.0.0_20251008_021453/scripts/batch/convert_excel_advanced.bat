@echo off
REM Advanced batch script to convert Excel files to Markdown format
REM This script provides options for converting all files or individual files

echo ========================================
echo CodeCritique - Advanced Excel Converter
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if the conversion script exists
if not exist "convert_excel_to_markdown.py" (
    echo ERROR: convert_excel_to_markdown.py not found
    echo Please make sure you're running this script from the CodeCritique directory
    pause
    exit /b 1
)

:MENU
echo.
echo Please select an option:
echo 1. Convert ALL Excel files to Markdown
echo 2. Convert a specific Excel file
echo 3. List available Excel files
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto CONVERT_ALL
if "%choice%"=="2" goto CONVERT_SPECIFIC
if "%choice%"=="3" goto LIST_FILES
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
goto MENU

:CONVERT_ALL
echo.
echo Converting all Excel files to Markdown format...
echo.
python convert_excel_to_markdown.py --all
if errorlevel 1 (
    echo.
    echo ERROR: Conversion failed
    pause
    goto MENU
)
echo.
echo All files converted successfully!
pause
goto MENU

:CONVERT_SPECIFIC
echo.
echo Available Excel files:
echo.
dir /s /b checklists\excel\*.xlsx 2>nul
if errorlevel 1 (
    echo No Excel files found in checklists\excel\ directory
    pause
    goto MENU
)
echo.
set /p excel_file="Enter the full path to the Excel file: "
if not exist "%excel_file%" (
    echo ERROR: File not found: %excel_file%
    pause
    goto MENU
)
echo.
echo Converting %excel_file%...
python convert_excel_to_markdown.py --excel "%excel_file%"
if errorlevel 1 (
    echo.
    echo ERROR: Conversion failed
    pause
    goto MENU
)
echo.
echo File converted successfully!
pause
goto MENU

:LIST_FILES
echo.
echo Excel files in checklists\excel\ directory:
echo.
dir /s /b checklists\excel\*.xlsx 2>nul
if errorlevel 1 (
    echo No Excel files found
)
echo.
echo Markdown files in checklists\markdown\ directory:
echo.
dir /s /b checklists\markdown\*.md 2>nul
if errorlevel 1 (
    echo No Markdown files found
)
pause
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0
