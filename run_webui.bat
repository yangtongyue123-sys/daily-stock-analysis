@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo Starting Web panel at http://127.0.0.1:8000
".venv\Scripts\python.exe" main.py --webui-only
pause
