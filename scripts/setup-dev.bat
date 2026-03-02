@echo off
setlocal EnableDelayedExpansion
REM CodeReview - Development environment setup (Windows CMD)
REM Run from project root: scripts\setup-dev.bat
REM Env: PIP_PROXY, PIP_PROXY_USER, PIP_PROXY_PASS, APP_NAME

cd /d "%~dp0\.."
set "PROJECT_ROOT=%CD%"

echo === CodeReview Dev Setup ===
echo Project root: %PROJECT_ROOT%
echo.

REM Prompt for proxy (use env if set)
if "%PIP_PROXY%"=="" (
  set /p "PIP_PROXY=Proxy URL (e.g. http://proxy:8080) [Enter to skip]: "
)
if not "%PIP_PROXY%"=="" (
  if "%PIP_PROXY_USER%"=="" set /p "PIP_PROXY_USER=Proxy username [Enter to skip]: "
  if not "!PIP_PROXY_USER!"=="" (
    if "%PIP_PROXY_PASS%"=="" set /p "PIP_PROXY_PASS=Proxy password [Enter to skip]: "
  )
)

REM Build proxy URL with auth (URL-encode via Python, reads from env to avoid special-char issues)
if not "%PIP_PROXY%"=="" (
  if not "%PIP_PROXY_USER%"=="" if not "%PIP_PROXY_PASS%"=="" (
    for /f "delims=" %%a in ('python -c "import os,urllib.parse,re; p=os.environ.get('PIP_PROXY',''); u=os.environ.get('PIP_PROXY_USER',''); pw=os.environ.get('PIP_PROXY_PASS',''); m=re.match(r'^(https?)://(.+)', p) if p and u and pw else None; print(m.group(1)+'://'+urllib.parse.quote(u,safe='')+':'+urllib.parse.quote(pw,safe='')+'@'+m.group(2)) if m else p" 2^>nul') do set "PIP_PROXY=%%a"
  )
)

REM Prompt for Name, Venv, Build
if "%APP_NAME%"=="" set /p "APP_NAME=App name to restore (e.g. CodeCritique) [Enter to skip]: "
set /p "DO_VENV=Create virtual environment (.venv)? [y/N]: "
set /p "DO_BUILD=Run Electron build after setup? [y/N]: "

if /i "%DO_VENV:~0,1%"=="y" set VENV=1
if /i "%DO_BUILD:~0,1%"=="y" set BUILD=1

if defined PIP_PROXY echo Pip proxy: %PIP_PROXY%
if not "%APP_NAME%"=="" echo Restore app name to: %APP_NAME%
if defined VENV echo Create venv (.venv) for dependencies
if defined BUILD echo Run Electron build (build:win) after setup
echo.

REM Restore app name (call PowerShell script)
if not "%APP_NAME%"=="" (
  echo --- Restore app name ---
  powershell -ExecutionPolicy Bypass -File "%~dp0restore-name.ps1" -Name "%APP_NAME%"
  if errorlevel 1 echo   Restore app name failed (continuing)
  echo.
)

REM Python
echo --- Python ---
where python >nul 2>&1
if %errorlevel% equ 0 (
  set "PYTHON_CMD=python"
) else (
  where py >nul 2>&1
  if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
  ) else (
    echo ERROR: Python 3.8+ required. Install from https://www.python.org/
    exit /b 1
  )
)

%PYTHON_CMD% --version

REM Create venv if requested
if defined VENV (
  if not exist ".venv" (
    echo Creating venv at .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (echo   Venv creation failed - continuing) else (echo   Created)
  ) else (
    echo Venv .venv exists
  )
  set "PYTHON_CMD=.venv\Scripts\python.exe"
)

REM Install Python deps
echo Installing Python dependencies...
set "PIP_EXTRA=-q"
if not defined VENV if "%VIRTUAL_ENV%"=="" set "PIP_EXTRA=--user -q"
if defined PIP_PROXY set "PIP_EXTRA=!PIP_EXTRA! --proxy %PIP_PROXY%"
"%PYTHON_CMD%" -m pip install --upgrade pip %PIP_EXTRA%
if errorlevel 1 echo   pip upgrade failed (continuing)
"%PYTHON_CMD%" -m pip install -r requirements.txt %PIP_EXTRA%
if errorlevel 1 (echo   pip install failed - continuing) else (echo   OK)
if defined VENV echo Activate venv: .venv\Scripts\activate.bat
echo.

REM Checklist migration (Excel -> Markdown)
echo --- Checklist migration (Excel -^> Markdown) ---
if exist "scripts\py\auto_update_checklists.py" (
  "%PYTHON_CMD%" scripts\py\auto_update_checklists.py
  if errorlevel 1 (
    echo   Checklist migration failed (continuing). Run: python scripts/py/auto_update_checklists.py
  ) else (
    echo   OK
  )
) else (
  echo   auto_update_checklists.py not found, skipping
)
echo.

REM Node
echo --- Node.js ---
where node >nul 2>&1
if %errorlevel% equ 0 (
  for /f "tokens=2 delims=v." %%a in ('node -v 2^>nul') do set NODE_VER=%%a
  if defined NODE_VER if !NODE_VER! geq 18 (
    echo Node found
    echo Installing npm dependencies...
    call npm install --silent
    if errorlevel 1 (echo   npm install failed - continuing) else (echo   OK)
  ) else (
    echo Node 18+ recommended. Current: node -v
    echo Skipping npm install. Run 'npm install' when ready.
  )
) else (
  echo Node.js not found. Optional for web-only dev.
  echo Install from https://nodejs.org/ for Electron.
)
echo.

REM Data dir
if not exist "data" mkdir data
echo Data dir: %PROJECT_ROOT%\data
echo.

REM Electron build (resilient: setup completes even if build fails)
if defined BUILD (
  echo --- Electron build (build:win) ---
  where node >nul 2>&1
  if %errorlevel% equ 0 (
    call npm run build:win
    if errorlevel 1 (
      echo   Electron build failed - setup continues
      echo   Run "npm run build:win" manually later. Or "npm run build:win:pyonly" for PyInstaller-only.
      echo   Common causes: Python 3.9+, npm install, proxy/network, disk space.
    ) else (
      echo   OK
    )
  ) else (
    echo Node.js required for build. Skipping.
  )
  echo.
)

echo === Setup complete ===
echo.
echo Run options:
echo   Web only:     %PYTHON_CMD% app.py --dev-server
echo   Web (prod):   %PYTHON_CMD% app.py
echo   Electron:     npm start
echo   Docker:       docker compose up
echo.

endlocal
