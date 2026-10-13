@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo Starting built-in scheduler (daily). Keep this window open.
".venv\Scripts\python.exe" main.py --schedule
pause
