@echo off
REM Batch script to convert Excel files to Markdown format
REM This script uses the existing convert_excel_to_markdown.py script

echo ========================================
echo CodeCritique - Excel to Markdown Converter
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

echo Converting all Excel files to Markdown format...
echo.

REM Run the conversion script
python convert_excel_to_markdown.py --all

if errorlevel 1 (
    echo.
    echo ERROR: Conversion failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo Conversion completed successfully!
echo ========================================
echo.
echo Excel files have been converted to Markdown format in:
echo - checklists\markdown\ folder
echo.
echo You can now use the CodeCritique application with the updated checklists.
echo.

REM Ask if user wants to start the application
set /p start_app="Do you want to start the CodeCritique application now? (y/n): "
if /i "%start_app%"=="y" (
    echo.
    echo Starting CodeCritique application...
    echo The application will be available at: http://localhost:5000
    echo Press Ctrl+C to stop the application
    echo.
    python app.py
) else (
    echo.
    echo You can start the application later by running: python app.py
)

pause
