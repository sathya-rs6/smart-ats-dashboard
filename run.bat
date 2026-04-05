@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Resume Analyzer RAG - Robust Startup
echo ========================================
echo.

echo Activating virtual environment...
set "VENV_PATH=venv"
if not exist "venv\Scripts\activate.bat" (
    if exist "..\venv\Scripts\activate.bat" (
        set "VENV_PATH=..\venv"
    )
)

if exist "!VENV_PATH!\Scripts\activate.bat" (
    call !VENV_PATH!\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

echo.
echo Checking for existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo [INFO] Cleaning up existing process - PID: %%a - on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

echo Starting backend server in background...
echo.
echo  App will be available at: http://localhost:8000
echo  The browser will open automatically once the server is ready.
echo.

:: Start backend in a separate minimized window
start /min "Resume Analyzer Backend" python backend/main.py

:: Wait for server to be ready
python wait_for_server.py --timeout 300

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Server is ready. Opening browser...
    start "" "http://localhost:8000"
) else (
    echo.
    echo [ERROR] Server failed to start or health check timed out.
    echo Please check logs/app.log for details.
    pause
    exit /b 1
)

echo.
echo Press any key to EXIT this script (the backend will keep running).
pause >nul
