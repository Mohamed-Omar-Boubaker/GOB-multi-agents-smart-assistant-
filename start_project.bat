@echo off
title GOB Edge AI - Launcher
color 0A

echo.
echo  ========================================
echo     GOB Edge AI - Starting Project
echo  ========================================
echo.

:: === Find project root (the folder containing backend/ and agent-ui/) ===
set "PROJECT_ROOT=%~dp0"
:: If this .bat is placed at the project root, PROJECT_ROOT is correct.
:: If not, update the line below manually:
:: set "PROJECT_ROOT=C:\path\to\gob-edge-ai-main"

set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%agent-ui"
set "VENV_DIR=%PROJECT_ROOT%venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

:: === Check project structure ===
if not exist "%BACKEND_DIR%" (
    echo [ERROR] backend/ folder not found at: %BACKEND_DIR%
    echo         Place this file in the project root folder.
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] agent-ui/ folder not found at: %FRONTEND_DIR%
    pause
    exit /b 1
)

:: === Check .env file ===
if not exist "%BACKEND_DIR%\.env" (
    echo [WARN] backend/.env not found. Copying from .env.example ...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo [INFO] Created backend/.env - Edit it to add your API keys!
    echo.
)

:: === Check virtual environment ===
if not exist "%VENV_ACTIVATE%" (
    echo [INFO] Virtual environment not found. Creating it now...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Make sure Python is installed.
        pause
        exit /b 1
    )
    call "%VENV_ACTIVATE%"
    echo [INFO] Installing Python dependencies...
    pip install -r "%BACKEND_DIR%\requirements.txt"
    echo [INFO] Dependencies installed.
) else (
    call "%VENV_ACTIVATE%"
)

:: === Check node_modules ===
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [INFO] node_modules not found. Running npm install...
    cd /d "%FRONTEND_DIR%"
    npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Make sure Node.js is installed.
        pause
        exit /b 1
    )
)

echo.
echo  [1/2] Starting Backend (FastAPI on port 8000)...
start "GOB Backend" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%PROJECT_ROOT%" && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo  [2/2] Starting Frontend (Vite on port 5173)...
start "GOB Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo  ========================================
echo     Both services are starting!
echo  ----------------------------------------
echo     Backend:  http://localhost:8000
echo     API Docs: http://localhost:8000/docs
echo     Frontend: https://localhost:5173
echo  ========================================
echo.
echo  Close the two terminal windows to stop.
echo.
pause
