@echo off
echo ========================================
echo CodeCritique - Manual Dependency Installation
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

echo Virtual environment activated!
echo.

echo Installing dependencies with advanced proxy detection...
python proxy_setup.py
if errorlevel 1 (
    echo.
    echo Manual installation options:
    echo 1. Try without proxy: pip install -r requirements.txt
    echo 2. Try with specific proxy: pip install --proxy http://your-proxy:port -r requirements.txt
    echo 3. Try with trusted hosts: pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo You can now run CodeCritique using start.bat
echo.
pause
