@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if not exist "logs" mkdir "logs"
echo [run] full analysis (watchlist + market review) >> "logs\scheduled_run.log"
rem 按需求：这里只做分析并推送，不跑任何策略回测。
rem 如需同时跑 ETF 轮动信号（会含回测），把下面第二行取消注释即可。
rem echo [run] ETF rotation signals >> "logs\scheduled_run.log"
rem ".venv\Scripts\python.exe" main.py --etf-rotation >> "logs\scheduled_run.log" 2>&1
".venv\Scripts\python.exe" main.py >> "logs\scheduled_run.log" 2>&1
set RC=%ERRORLEVEL%
echo done: analysis=%RC% >> "logs\scheduled_run.log"
exit /b %RC%
