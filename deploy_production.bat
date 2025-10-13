@echo off
REM Production deployment script for CodeCritique
REM This script provides options for running CodeCritique in production

echo CodeCritique Production Deployment Options
echo =========================================
echo.
echo Choose your deployment method:
echo 1. Flask Development Server (Production Mode)
echo 2. Waitress WSGI Server (Recommended for Windows)
echo 3. Gunicorn WSGI Server (Linux/Mac)
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo Starting Flask in production mode...
    python app.py --production --no-browser --host 0.0.0.0 --port 5000
) else if "%choice%"=="2" (
    echo Installing Waitress if not available...
    pip install waitress
    echo Starting Waitress WSGI server...
    waitress-serve --host=0.0.0.0 --port=5000 wsgi:application
) else if "%choice%"=="3" (
    echo Installing Gunicorn if not available...
    pip install gunicorn
    echo Starting Gunicorn WSGI server...
    gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application
) else (
    echo Invalid choice. Please run the script again.
)

pause
