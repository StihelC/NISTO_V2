@echo off
REM NISTO Web Application - Master Test Runner (Batch Version)
REM Simple batch script to run tests

setlocal

set TARGET=%1
if "%TARGET%"=="" set TARGET=all

echo.
echo ================================================================
echo   NISTO Web Application Test Suite
echo ================================================================
echo.
echo Target: %TARGET%
echo.

if /i "%TARGET%"=="frontend" goto :run_frontend
if /i "%TARGET%"=="backend" goto :run_backend
if /i "%TARGET%"=="all" goto :run_all

echo Invalid target: %TARGET%
echo Valid targets: all, frontend, backend
echo.
echo Usage: run-tests.bat [target]
echo   run-tests.bat           - Run all tests
echo   run-tests.bat frontend  - Run frontend tests only
echo   run-tests.bat backend   - Run backend tests only
exit /b 1

:run_frontend
echo ================================================================
echo   Running Frontend Tests
echo ================================================================
cd frontend
npm test -- --run
set FRONTEND_EXIT=%ERRORLEVEL%
cd ..
if %FRONTEND_EXIT% neq 0 (
    echo Frontend tests FAILED!
    exit /b %FRONTEND_EXIT%
)
echo Frontend tests PASSED!
goto :end

:run_backend
echo ================================================================
echo   Running Backend Tests
echo ================================================================
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
python -m pytest -q
set BACKEND_EXIT=%ERRORLEVEL%
call venv\Scripts\deactivate.bat 2>nul
cd ..
if %BACKEND_EXIT% neq 0 (
    echo Backend tests FAILED!
    exit /b %BACKEND_EXIT%
)
echo Backend tests PASSED!
goto :end

:run_all
echo Running all tests...
echo.

echo ================================================================
echo   Running Frontend Tests
echo ================================================================
cd frontend
npm test -- --run
set FRONTEND_EXIT=%ERRORLEVEL%
cd ..

echo.
echo ================================================================
echo   Running Backend Tests
echo ================================================================
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
python -m pytest -q
set BACKEND_EXIT=%ERRORLEVEL%
call venv\Scripts\deactivate.bat 2>nul
cd ..

echo.
echo ================================================================
echo   Test Summary
echo ================================================================
if %FRONTEND_EXIT% equ 0 (
    echo Frontend: PASSED
) else (
    echo Frontend: FAILED
)

if %BACKEND_EXIT% equ 0 (
    echo Backend: PASSED
) else (
    echo Backend: FAILED
)

set /a TOTAL_EXIT=%FRONTEND_EXIT%+%BACKEND_EXIT%
if %TOTAL_EXIT% equ 0 (
    echo.
    echo All tests PASSED! 🎉
) else (
    echo.
    echo Some tests FAILED! 💥
)
exit /b %TOTAL_EXIT%

:end
echo.
echo Test execution completed.
endlocal
