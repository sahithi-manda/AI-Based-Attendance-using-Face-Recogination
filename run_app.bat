@echo off
setlocal

echo ==========================================
echo   AI Attendance System - Auto Setup
echo ==========================================

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.11 by running this command in a terminal:
    echo winget install -e --id Python.Python.3.11
    echo After installing, please RESTART this file.
    pause
    exit /b
)

:: 2. Check if venv folder already exists
if not exist "venv" (
    echo [INFO] Creating virtual environment (this may take a minute)...
    python -m venv venv
)

:: 3. Activate venv and install requirements
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

echo [INFO] Installing/Updating dependencies...
pip install -r requirements.txt

:: 4. Run the application
echo [INFO] Launching Attendance System...
python main.py

echo ==========================================
echo   Application Closed.
echo ==========================================
pause
