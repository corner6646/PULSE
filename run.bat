@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m pulse.main --once
pause
