@echo off
echo Cleaning Vite cache and restarting development server...

REM Kill any existing Node processes
taskkill /F /IM node.exe >nul 2>&1

REM Remove Vite cache directories
if exist "node_modules\.vite" rd /s /q "node_modules\.vite"
if exist ".vite" rd /s /q ".vite"

REM Clear npm cache
npm cache clean --force

echo Starting development server with fresh cache...
npx vite --force --clearScreen false

echo.
echo If you see "504 Outdated Optimize Dep" errors:
echo 1. Press Ctrl+C to stop the server
echo 2. Run this script again
echo 3. Or refresh your browser (Ctrl+F5)
