@echo off
echo ========================================
echo Starting CodeCritique
echo ========================================
echo.

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Starting CodeCritique server...
echo.
echo The application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
