@echo off
echo Starting NISTO Backend Server...
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Virtual environment activated
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
