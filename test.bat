@echo on
setlocal enabledelayedexpansion
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo [INFO] Cleaning up existing process (PID: %%a) on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
