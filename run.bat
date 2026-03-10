@echo off
echo ========================================
echo Resume Analyzer RAG 
echo ========================================

echo Activating virtual environment...
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Could not find virtual environment.
)

echo Starting Backend Server...
python backend/main.py

pause
