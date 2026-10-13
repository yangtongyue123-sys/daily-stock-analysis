@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if not exist "logs" mkdir "logs"
echo [1/2] full analysis (watchlist + market review) >> "logs\scheduled_run.log"
".venv\Scripts\python.exe" main.py >> "logs\scheduled_run.log" 2>&1
set RC1=%ERRORLEVEL%
echo [2/2] ETF rotation signals (no LLM needed) >> "logs\scheduled_run.log"
".venv\Scripts\python.exe" main.py --etf-rotation >> "logs\scheduled_run.log" 2>&1
set RC2=%ERRORLEVEL%
echo done: analysis=%RC1% etf=%RC2% >> "logs\scheduled_run.log"
exit /b %RC1%
