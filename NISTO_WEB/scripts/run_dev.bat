@echo off
setlocal EnableDelayedExpansion

:: Get the root directory (parent of scripts)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "BACKEND_DIR=%ROOT_DIR%\backend"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "VENV_DIR=%BACKEND_DIR%\venv"

echo ==========================================
echo NISTO Development Server Startup
echo ==========================================

:: Check if Python is available
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating Python virtual environment...
    cd /d "%BACKEND_DIR%"
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

:: Install Python dependencies if requirements.txt is newer than venv
echo Checking Python dependencies...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

:: Check if Node.js/npm is available
where npm >nul 2>&1
if !errorlevel! neq 0 (
    echo Error: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    echo Make sure to restart your command prompt after installation
    pause
    exit /b 1
)

:: Install frontend dependencies if node_modules doesn't exist
if not exist "%FRONTEND_DIR%\node_modules" (
    echo Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if !errorlevel! neq 0 (
        echo Error: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    echo Frontend dependencies installed successfully!
)

:: Kill any existing processes on our ports
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing process %%a on port 8000
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo Killing process %%a on port 5173
    taskkill /f /pid %%a >nul 2>&1
)
:: Also kill any Node.js/npm processes that might be running
taskkill /f /im node.exe >nul 2>&1 || echo No Node processes to kill
timeout /t 2 /nobreak >nul

:: Start backend in virtual environment
echo Starting FastAPI backend on port 8000...
cd /d "%BACKEND_DIR%"
start "NISTO Backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting React frontend on port 5173...
cd /d "%FRONTEND_DIR%"
start "NISTO Frontend" cmd /k "npm run dev"

:: Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo Services started successfully!
echo ==========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173 (or next available port)
echo API Docs: http://localhost:8000/docs
echo.
echo NOTE: If port 5173 is busy, Vite will use the next available port
echo Check the frontend terminal window for the actual URL
echo.
echo Press Ctrl+C in each terminal window to stop the services
echo Or close this window to keep them running in background
echo ==========================================

pause
