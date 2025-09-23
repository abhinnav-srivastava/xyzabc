@echo off
echo ========================================
echo CodeCritique Setup Script
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created!
echo.

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated!
echo.

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully!
echo.

echo Converting Excel files to Markdown...
python convert_excel_to_markdown.py --all
if errorlevel 1 (
    echo WARNING: Failed to convert Excel files (this is optional)
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To start CodeCritique:
echo 1. Run: start.bat
echo 2. Or manually: .venv\Scripts\activate && python app.py
echo 3. Open browser to: http://localhost:5000
echo.
pause
